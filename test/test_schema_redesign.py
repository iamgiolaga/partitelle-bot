"""The normalized schema (chat, setting, match, participant) built by the real migrations in a throwaway schema,
next to the legacy all_players table."""

import contextlib
import importlib.util
import io
import logging
import os
import re
import subprocess
import sys
import uuid
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
import pytest
import yoyo
from psycopg import errors, sql
from yoyo import get_backend, read_migrations

from db import migrate as db_migrate


@pytest.fixture(scope="module")
def schema():
    name = f"schema_redesign_{uuid.uuid4().hex[:8]}"
    with psycopg.connect(
        host=os.environ["PB_DB_HOST"],
        port=os.environ["PB_DB_PORT"],
        user=os.environ["PB_DB_USER"],
        password=os.environ["PB_DB_PASSWORD"],
        dbname=os.environ["PB_DB_NAME"],
        autocommit=True,
    ) as conn:
        mp = pytest.MonkeyPatch()
        mp.setattr(db_migrate, "db_schema", name)
        try:
            db_migrate.migrate()
            yield name
        finally:
            mp.undo()
            conn.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(name))
            )


@pytest.fixture
def db(schema):
    with psycopg.connect(
        host=os.environ["PB_DB_HOST"],
        port=os.environ["PB_DB_PORT"],
        user=os.environ["PB_DB_USER"],
        password=os.environ["PB_DB_PASSWORD"],
        dbname=os.environ["PB_DB_NAME"],
        options=f"-c search_path={schema}",
        autocommit=True,
    ) as conn:
        yield conn
        conn.execute("TRUNCATE chat CASCADE")


def add_chat(db, telegram_chat_id=1):
    return db.execute(
        "INSERT INTO chat (telegram_chat_id) VALUES (%s) RETURNING chat_uuid",
        [telegram_chat_id],
    ).fetchone()[0]


def add_match(db, chat_uuid, stopped=False):
    return db.execute(
        "INSERT INTO match (chat_uuid, starts_ts, target, stopped_ts) "
        "VALUES (%s, now(), 10, CASE WHEN %s THEN now() END) RETURNING match_uuid",
        [chat_uuid, stopped],
    ).fetchone()[0]


def add_participant(db, match_uuid, status="confirmed", position=1, **columns):
    columns = {"status": status, "position": position, **columns}
    names = sql.SQL(", ").join(map(sql.Identifier, columns))
    marks = sql.SQL(", ").join(sql.Placeholder() * len(columns))
    db.execute(
        sql.SQL("INSERT INTO participant (match_uuid, {}) VALUES (%s, {})").format(
            names, marks
        ),
        [match_uuid, *columns.values()],
    )


def test_the_legacy_table_is_still_there(db):
    assert db.execute("SELECT count(*) FROM all_players").fetchone() == (0,)


def test_setting_defaults_match_the_bot_defaults(db):
    chat_uuid = add_chat(db)
    row = db.execute(
        "INSERT INTO setting (chat_uuid) VALUES (%s) "
        "RETURNING language, timezone, default_target, default_weekday, default_time::text, "
        "default_pitch, default_description",
        [chat_uuid],
    ).fetchone()
    assert row == ("it", "Europe/Rome", 10, 3, "20:00:00", None, None)


@pytest.mark.parametrize(
    "column, value",
    [
        ("default_target", 1),
        ("default_target", 41),
        ("default_weekday", 0),
        ("default_weekday", 8),
    ],
)
def test_setting_values_out_of_range_are_rejected(db, column, value):
    chat_uuid = add_chat(db)
    with pytest.raises(errors.CheckViolation):
        db.execute(
            sql.SQL("INSERT INTO setting (chat_uuid, {}) VALUES (%s, %s)").format(
                sql.Identifier(column)
            ),
            [chat_uuid, value],
        )


def test_a_chat_has_a_single_setting_row(db):
    chat_uuid = add_chat(db)
    db.execute("INSERT INTO setting (chat_uuid) VALUES (%s)", [chat_uuid])
    with pytest.raises(errors.UniqueViolation):
        db.execute("INSERT INTO setting (chat_uuid) VALUES (%s)", [chat_uuid])


def test_a_telegram_chat_is_stored_once(db):
    add_chat(db, 7)
    with pytest.raises(errors.UniqueViolation):
        add_chat(db, 7)


def test_a_match_target_out_of_range_is_rejected(db):
    chat_uuid = add_chat(db)
    with pytest.raises(errors.CheckViolation):
        db.execute(
            "INSERT INTO match (chat_uuid, starts_ts, target) VALUES (%s, now(), 1)",
            [chat_uuid],
        )


def test_a_second_active_match_for_the_chat_is_rejected(db):
    chat_uuid = add_chat(db)
    add_match(db, chat_uuid)
    with pytest.raises(errors.UniqueViolation):
        add_match(db, chat_uuid)


def test_stopped_matches_do_not_count_as_active(db):
    chat_uuid = add_chat(db)
    add_match(db, chat_uuid, stopped=True)
    add_match(db, chat_uuid, stopped=True)
    add_match(db, chat_uuid)
    other_chat = add_chat(db, 2)
    add_match(db, other_chat)


def test_stopping_the_active_match_allows_a_new_one(db):
    chat_uuid = add_chat(db)
    match_uuid = add_match(db, chat_uuid)
    db.execute(
        "UPDATE match SET stopped_ts = now() WHERE match_uuid = %s", [match_uuid]
    )
    add_match(db, chat_uuid)


def test_active_match_view_hides_stopped_matches(db):
    chat_uuid = add_chat(db)
    add_match(db, chat_uuid, stopped=True)
    active = add_match(db, chat_uuid)
    rows = db.execute("SELECT match_uuid FROM active_match").fetchall()
    assert rows == [(active,)]


def test_team_requires_a_confirmed_participant(db):
    match_uuid = add_match(db, add_chat(db))
    add_participant(db, match_uuid, "confirmed", 1, display_name="Anna", team="black")
    for status in ("maybe", "waiting"):
        with pytest.raises(errors.CheckViolation):
            add_participant(db, match_uuid, status, 2, display_name="Bea", team="white")
    add_participant(db, match_uuid, "maybe", 2, display_name="Bea")


def test_display_names_differing_only_in_case_are_rejected_in_the_same_match(db):
    chat_uuid = add_chat(db)
    match_uuid = add_match(db, chat_uuid, stopped=True)
    add_participant(db, match_uuid, position=1, display_name="Giulia")
    with pytest.raises(errors.UniqueViolation):
        add_participant(db, match_uuid, position=2, display_name="gIULIA")
    # same name in another match, and participants without a name, are fine
    add_participant(db, add_match(db, chat_uuid), position=1, display_name="giulia")
    add_participant(db, match_uuid, position=3, telegram_user_id=1)
    add_participant(db, match_uuid, position=4, telegram_user_id=2)


def test_a_telegram_user_joins_a_match_once(db):
    match_uuid = add_match(db, add_chat(db))
    add_participant(db, match_uuid, position=1, telegram_user_id=5)
    with pytest.raises(errors.UniqueViolation):
        add_participant(db, match_uuid, position=2, telegram_user_id=5)


def test_updated_ts_changes_on_update_and_created_ts_does_not(db):
    chat_uuid = add_chat(db)
    before = db.execute(
        "SELECT created_ts, updated_ts FROM chat WHERE chat_uuid = %s", [chat_uuid]
    ).fetchone()
    db.execute("SELECT pg_sleep(0.01)")
    db.execute(
        "UPDATE chat SET telegram_chat_id = 99 WHERE chat_uuid = %s", [chat_uuid]
    )
    after = db.execute(
        "SELECT created_ts, updated_ts FROM chat WHERE chat_uuid = %s", [chat_uuid]
    ).fetchone()
    assert after[0] == before[0]
    assert after[1] > before[1]


@pytest.mark.parametrize("table", ["chat", "setting", "match", "participant"])
def test_every_table_has_the_updated_ts_trigger(db, table):
    assert db.execute(
        "SELECT count(*) FROM pg_trigger "
        "WHERE tgrelid = %s::regclass AND NOT tgisinternal AND tgname = %s",
        [table, f"{table}_set_updated_ts"],
    ).fetchone() == (1,)


def test_deleting_a_chat_cascades_to_everything_below_it(db):
    chat_uuid = add_chat(db)
    db.execute("INSERT INTO setting (chat_uuid) VALUES (%s)", [chat_uuid])
    match_uuid = add_match(db, chat_uuid)
    add_participant(db, match_uuid, display_name="Anna")

    db.execute("DELETE FROM chat WHERE chat_uuid = %s", [chat_uuid])

    for table in ("setting", "match", "participant"):
        assert db.execute(
            sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table))
        ).fetchone() == (0,)


def test_running_the_migrations_again_changes_nothing(schema, db, caplog):
    caplog.set_level(logging.INFO, logger="db.migrate")
    db_migrate.migrate()
    assert [
        (record.levelname, record.getMessage())
        for record in caplog.records
        if record.name == "db.migrate"
    ] == [("INFO", f"Schema '{schema}' is up to date: no migrations to apply")]


def test_the_standalone_migrate_command_logs_at_info(schema, db):
    """`python -m db.migrate` runs on its own before the bot starts: its messages must still be emitted."""
    result = subprocess.run(
        [sys.executable, "-m", "db.migrate"],
        cwd=Path(db_migrate.__file__).resolve().parent.parent,
        env={**os.environ, "PB_DB_SCHEMA": schema},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    timestamp = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}"
    lines = [
        re.sub(f"^{timestamp} - ", "", line) for line in result.stderr.splitlines()
    ]
    assert lines == [
        f"db.migrate - INFO - Schema '{schema}' is up to date: no migrations to apply"
    ]


# --- 0003: copy of the legacy all_players rows ---

COPY_MIGRATION_ID = "0003_copy_legacy_data"
ROME = ZoneInfo("Europe/Rome")
BAMBOO = (
    "Crespi Sport Village \n\nVia Carlo Valvassori Peroni, 48, 20133 \n"
    "Milano, MI, 02 266 3774 \nhttps://g.co/kgs/L9b6KZ"
)


def load_copy_migration():
    path = db_migrate.MIGRATIONS_DIR / f"{COPY_MIGRATION_ID}.py"
    spec = importlib.util.spec_from_file_location("copy_migration", path)
    module = importlib.util.module_from_spec(spec)
    # outside yoyo there is no collector for step()
    mp = pytest.MonkeyPatch()
    mp.setattr(yoyo, "step", lambda *args, **kwargs: None)
    try:
        spec.loader.exec_module(module)
    finally:
        mp.undo()
    return module


def rome_today():
    return datetime.now(ROME).date()


def day_text(days_from_today):
    target = rome_today() + timedelta(days=days_from_today)
    return "Mercoledì " + target.strftime("%d/%m/%Y")


def next_weekday_after_today(weekday):
    today = rome_today()
    return today + timedelta(days=(weekday - today.weekday()) % 7 or 7)


def legacy_row(chat_id, **columns):
    return {
        "chat_id": chat_id,
        "players": None,
        "day": day_text(7),
        "time": "21:00",
        "target": 10,
        "custom_message": None,
        "pitch": None,
        "bot_last_message_id": None,
        "teams": None,
        **columns,
    }


LEGACY_ROWS = [
    # players with maybe, case-insensitive team names, a ghost and a maybe player in the teams
    legacy_row(
        1,
        players=["anna", "Bea%is%maybe%present", "carlo", "Dina"],
        teams='{"black": ["Anna", "bea", "ghost"], "white": ["CARLO"]}',
        custom_message="portare la maglia",
        bot_last_message_id=555,
        target=12,
    ),
    legacy_row(2, day="venerdi", time="20", target=None, pitch=BAMBOO),
    legacy_row(3, day="boh", time="boh"),
    legacy_row(4, day="Mercoledì 11/05/2022", time="21:00"),
    legacy_row(5, day=day_text(-3), time="20:00"),
    legacy_row(6, players=["Mario", "mario", "Luca"]),
    legacy_row(7, day=day_text(7), time="9.30", pitch="Altro campo"),
    legacy_row(8, players=["%is%maybe%present", "", "Ugo"]),
    legacy_row(9, day="Mercoledì 11/05/2022", time="21:00", pitch=BAMBOO),
]


@pytest.fixture(scope="module")
def copied():
    """A schema migrated up to 0002, filled with legacy rows, then migrated to 0003."""
    name = f"schema_copy_{uuid.uuid4().hex[:8]}"
    params = dict(
        host=os.environ["PB_DB_HOST"],
        port=os.environ["PB_DB_PORT"],
        user=os.environ["PB_DB_USER"],
        password=os.environ["PB_DB_PASSWORD"],
        dbname=os.environ["PB_DB_NAME"],
    )
    db_migrate.create_schema(name)
    backend = get_backend(db_migrate.build_uri(name))
    pending = backend.to_apply(read_migrations(str(db_migrate.MIGRATIONS_DIR)))
    backend.apply_migrations(pending.filter(lambda m: m.id != COPY_MIGRATION_ID))
    with psycopg.connect(
        **params, options=f"-c search_path={name}", autocommit=True
    ) as conn:
        try:
            for row in LEGACY_ROWS:
                conn.execute(
                    "INSERT INTO all_players (chat_id, players, day, time, target, custom_message, "
                    "pitch, bot_last_message_id, teams) VALUES (%(chat_id)s, %(players)s, %(day)s, "
                    "%(time)s, %(target)s, %(custom_message)s, %(pitch)s, %(bot_last_message_id)s, "
                    "%(teams)s::json)",
                    row,
                )
            before = conn.execute(
                "SELECT * FROM all_players ORDER BY chat_id"
            ).fetchall()
            pending = backend.to_apply(read_migrations(str(db_migrate.MIGRATIONS_DIR)))
            assert [m.id for m in pending] == [COPY_MIGRATION_ID]
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                backend.apply_migrations(pending)
            yield conn, before, out.getvalue()
        finally:
            conn.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(name))
            )


def copied_match(conn, chat_id):
    return conn.execute(
        "SELECT m.match_uuid, m.starts_ts, m.target, m.description, m.pitch, "
        "m.telegram_summary_message_id, m.stopped_ts, m.reminder_sent_ts "
        "FROM match m JOIN chat c USING (chat_uuid) WHERE c.telegram_chat_id = %s",
        [chat_id],
    ).fetchone()


def copied_participants(conn, chat_id):
    return conn.execute(
        "SELECT p.display_name, p.status::text, p.position, p.team::text, p.telegram_user_id "
        "FROM participant p JOIN match m USING (match_uuid) JOIN chat c USING (chat_uuid) "
        "WHERE c.telegram_chat_id = %s ORDER BY p.position",
        [chat_id],
    ).fetchall()


def rome(day, at=time(20, 0)):
    return datetime.combine(day, at, tzinfo=ROME)


def test_every_legacy_chat_gets_a_chat_a_setting_and_a_match(copied):
    conn, _, _ = copied
    assert conn.execute("SELECT count(*) FROM chat").fetchone() == (len(LEGACY_ROWS),)
    assert conn.execute("SELECT count(*) FROM setting").fetchone() == (
        len(LEGACY_ROWS),
    )
    assert conn.execute("SELECT count(*) FROM match").fetchone() == (len(LEGACY_ROWS),)


def test_match_columns_are_copied_with_the_target_default(copied):
    conn, _, _ = copied
    _, starts, target, description, pitch, summary, _, _ = copied_match(conn, 1)
    assert (target, description, pitch, summary) == (12, "portare la maglia", None, 555)
    assert starts == rome(rome_today() + timedelta(days=7), time(21, 0))
    assert copied_match(conn, 2)[2] == 10


def test_maybe_players_lose_the_suffix_and_positions_follow_the_array(copied):
    conn, _, _ = copied
    assert [(n, s, p) for n, s, p, _, _ in copied_participants(conn, 1)] == [
        ("anna", "confirmed", 1),
        ("Bea", "maybe", 2),
        ("carlo", "confirmed", 3),
        ("Dina", "confirmed", 4),
    ]
    assert all(user is None for *_, user in copied_participants(conn, 1))


def test_teams_are_set_only_for_matched_confirmed_players(copied):
    conn, _, out = copied
    assert [(n, t) for n, _, _, t, _ in copied_participants(conn, 1)] == [
        ("anna", "black"),
        ("Bea", None),
        ("carlo", "white"),
        ("Dina", None),
    ]
    # ghost and the maybe player
    assert "chat 1: 2 team name(s) matched no confirmed player" in out


def test_null_players_give_no_participants(copied):
    conn, _, _ = copied
    assert copied_participants(conn, 3) == []


def test_empty_names_are_skipped_and_positions_stay_contiguous(copied):
    conn, _, _ = copied
    assert [(n, p) for n, _, p, _, _ in copied_participants(conn, 8)] == [("Ugo", 1)]


def test_weekday_only_day_means_the_next_such_weekday_at_the_given_time(copied):
    conn, _, out = copied
    assert copied_match(conn, 2)[1] == rome(next_weekday_after_today(4))
    assert "chat 2: weekday-only day, fallback used" in out
    assert "chat 2: unreadable time" not in out


def test_unreadable_day_and_time_mean_next_wednesday_at_20(copied):
    conn, _, out = copied
    assert copied_match(conn, 3)[1] == rome(next_weekday_after_today(2))
    assert "chat 3: unreadable day, fallback used" in out
    assert "chat 3: unreadable time, fallback used" in out


def test_dotted_time_is_read(copied):
    conn, _, _ = copied
    assert copied_match(conn, 7)[1] == rome(
        rome_today() + timedelta(days=7), time(9, 30)
    )


def test_a_2022_match_is_stopped_and_its_reminder_is_marked_sent(copied):
    conn, _, _ = copied
    *_, stopped, reminder = copied_match(conn, 4)
    assert stopped is not None and reminder is not None


def test_a_recent_past_match_is_active_with_its_reminder_marked_sent(copied):
    conn, _, _ = copied
    *_, stopped, reminder = copied_match(conn, 5)
    assert stopped is None and reminder is not None


def test_a_future_match_has_neither_stopped_nor_reminder(copied):
    conn, _, _ = copied
    *_, stopped, reminder = copied_match(conn, 7)
    assert (stopped, reminder) == (None, None)


def test_bamboo_pitch_becomes_the_default_pitch_of_the_chat(copied):
    conn, _, _ = copied
    rows = dict(
        conn.execute(
            "SELECT c.telegram_chat_id, s.default_pitch FROM setting s JOIN chat c USING (chat_uuid)"
        ).fetchall()
    )
    assert rows[2] == BAMBOO
    assert [chat for chat, pitch in rows.items() if pitch is not None] == [2]
    assert copied_match(conn, 2)[4] == BAMBOO


def test_stopped_match_leaves_its_chat_without_a_default_pitch(copied):
    conn, _, _ = copied
    match = copied_match(conn, 9)
    assert match[4] == BAMBOO
    assert match[6] is not None
    assert conn.execute(
        "SELECT s.default_pitch FROM setting s JOIN chat c USING (chat_uuid) "
        "WHERE c.telegram_chat_id = 9"
    ).fetchone() == (None,)


def test_names_colliding_case_insensitively_keep_the_first(copied):
    conn, _, out = copied
    assert [(n, p) for n, _, p, _, _ in copied_participants(conn, 6)] == [
        ("Mario", 1),
        ("Luca", 2),
    ]
    assert "chat 6: 1 duplicate name(s) skipped" in out


def test_active_match_counts_the_non_stale_rows(copied):
    conn, _, _ = copied
    assert conn.execute("SELECT count(*) FROM active_match").fetchone() == (
        len(LEGACY_ROWS) - 2,
    )


def test_the_legacy_table_is_unchanged_by_the_copy(copied):
    conn, before, _ = copied
    assert (
        conn.execute("SELECT * FROM all_players ORDER BY chat_id").fetchall() == before
    )


def test_the_summary_and_anomalies_never_print_names_or_texts(copied):
    _, _, out = copied
    assert (
        "0003 copied 9 chat(s): 2 match(es) stopped, 3 reminder(s) marked as sent"
        in out
    )
    for private in ("anna", "Mario", "Ugo", "boh", "Altro campo"):
        assert private not in out


def test_the_copy_is_a_no_op_on_an_empty_legacy_table(db):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        load_copy_migration().copy_legacy_rows(db.cursor().connection, rome_today())
    assert out.getvalue() == ""
    assert db.execute("SELECT count(*) FROM chat").fetchone() == (0,)


@pytest.mark.parametrize(
    "day, at, expected",
    [
        ("Mercoledì 28/10/2026", "21:00", (date(2026, 10, 28), time(21, 0))),
        ("mercoledi 28/10/2026", "9:05", (date(2026, 10, 28), time(9, 5))),
        ("SABATO 31/10/2026", "21.30", (date(2026, 10, 31), time(21, 30))),
        ("25/10/2026", "20", (date(2026, 10, 25), time(20, 0))),
        ("lunedì", "19:30", (date(2026, 11, 2), time(19, 30))),
        ("Lunedi", "24:00", (date(2026, 11, 2), time(20, 0))),
        ("Mercoledì", "", (date(2026, 10, 28), time(20, 0))),
        ("prossima settimana", None, (date(2026, 10, 28), time(20, 0))),
        (None, "21:00", (date(2026, 10, 28), time(21, 0))),
    ],
)
def test_legacy_day_and_time_parsing_on_a_fixed_run_date(day, at, expected):
    starts, _ = load_copy_migration().resolve_starts(day, at, date(2026, 10, 26))
    assert (starts.date(), starts.time()) == expected
    assert starts.tzinfo == ROME
