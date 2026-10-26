"""The normalized schema (chat, setting, match, participant) built by the real migrations in a throwaway schema,
next to the legacy all_players table."""

import os
import uuid

import psycopg
import pytest
from psycopg import errors, sql

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


def test_running_the_migrations_again_changes_nothing(schema, db, capsys):
    db_migrate.migrate()
    assert "up to date" in capsys.readouterr().out
