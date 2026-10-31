"""Real-Postgres support for the feature tests (harness only: the .feature files never see any of this)."""

import os

import psycopg
import pytest
from psycopg import sql


def _params(database):
    return {
        "host": os.environ["PB_DB_HOST"],
        "port": os.environ["PB_DB_PORT"],
        "user": os.environ["PB_DB_USER"],
        "password": os.environ["PB_DB_PASSWORD"],
        "dbname": database,
    }


def _connect(database, schema=None):
    options = {"options": f"-c search_path={schema}"} if schema else {}
    conn = psycopg.connect(
        connect_timeout=5, autocommit=True, **_params(database), **options
    )
    return conn


def prepare_database():
    """Create the test database if missing, then rebuild the bot schema through the real migrations."""
    name = os.environ["PB_DB_NAME"]
    if not name.endswith("_test"):
        pytest.fail(
            f"Refusing to run feature tests on database '{name}': the name must end with '_test' "
            "because the schema is dropped and recreated.",
            pytrace=False,
        )
    try:
        admin = _connect("postgres")
    except psycopg.OperationalError as error:
        pytest.fail(
            "Cannot reach Postgres for the feature tests "
            f"({os.environ['PB_DB_HOST']}:{os.environ['PB_DB_PORT']}). "
            f"Run `docker compose up -d --wait` first.\n{error}",
            pytrace=False,
        )
    cur = admin.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", [name])
    if cur.fetchone() is None:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    admin.close()

    schema = os.environ["PB_DB_SCHEMA"]
    conn = _connect(name)
    conn.cursor().execute(
        sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema))
    )
    conn.close()

    # imported only now: conf.conf reads the environment at import time (set by test/conftest.py)
    from db.migrate import migrate

    migrate()


class Database:
    """Independent connection used by the harness to reset and inspect the persisted state."""

    def __init__(self):
        self.conn = _connect(os.environ["PB_DB_NAME"], os.environ["PB_DB_SCHEMA"])

    def truncate(self):
        with self.conn.cursor() as cur:
            cur.execute("TRUNCATE chat CASCADE")

    def _set_match(self, chat_id, column, value):
        with self.conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    "UPDATE match SET {} = %s WHERE stopped_ts IS NULL AND chat_uuid = "
                    "(SELECT chat_uuid FROM chat WHERE telegram_chat_id = %s)"
                ).format(sql.Identifier(column)),
                [value, chat_id],
            )

    def _active_match_uuid(self, chat_id):
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT m.match_uuid FROM match m JOIN chat c USING (chat_uuid) "
                "WHERE c.telegram_chat_id = %s AND m.stopped_ts IS NULL",
                [chat_id],
            )
            row = cur.fetchone()
        assert row is not None, f"seeding a match that does not exist (chat {chat_id})"
        return row[0]

    def set_target(self, chat_id, target):
        self._set_match(chat_id, "target", target)

    def set_pitch(self, chat_id, pitch):
        self._set_match(chat_id, "pitch", pitch)

    def set_default_pitch(self, chat_id, pitch):
        """The chat's setting row, as the setup of the chat would leave it."""
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat (telegram_chat_id) VALUES (%s) "
                "ON CONFLICT (telegram_chat_id) DO UPDATE "
                "SET telegram_chat_id = EXCLUDED.telegram_chat_id RETURNING chat_uuid",
                [chat_id],
            )
            chat_uuid = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO setting (chat_uuid, default_pitch) VALUES (%s, %s)",
                [chat_uuid, pitch],
            )

    def set_players(self, chat_id, players):
        """`players` is a list of (name, is_maybe), in order."""
        match_uuid = self._active_match_uuid(chat_id)
        with self.conn.cursor() as cur:
            cur.execute("DELETE FROM participant WHERE match_uuid = %s", [match_uuid])
            for position, (name, is_maybe) in enumerate(players, start=1):
                cur.execute(
                    "INSERT INTO participant (match_uuid, display_name, status, position) "
                    "VALUES (%s, %s, %s::participant_status, %s)",
                    [match_uuid, name, "maybe" if is_maybe else "confirmed", position],
                )

    def set_teams(self, chat_id, black, white):
        """Teams are a property of the confirmed participants: they must be seeded first."""
        match_uuid = self._active_match_uuid(chat_id)
        with self.conn.cursor() as cur:
            for colour, names in (("black", black), ("white", white)):
                for name in names:
                    cur.execute(
                        "UPDATE participant SET team = %s::team_colour WHERE match_uuid = %s "
                        "AND display_name = %s AND status = 'confirmed'",
                        [colour, match_uuid, name],
                    )
                    assert cur.rowcount == 1, f"{name!r} is not a confirmed player"

    def fetch_match(self, chat_id):
        """The active match of a chat as a dict of test values, or None when there is none.

        players: None when there are none, else a list of (name, is_maybe) in position order;
        teams: None or {"black": [...], "white": [...]} (members in position order); day and time as
        the bot renders them (Europe/Rome).
        """
        from domain.schedule import TIMEZONE, format_day, format_time

        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT m.match_uuid, m.starts_ts, m.target, m.description, m.pitch, "
                "m.telegram_summary_message_id FROM match m JOIN chat c USING (chat_uuid) "
                "WHERE c.telegram_chat_id = %s AND m.stopped_ts IS NULL",
                [chat_id],
            )
            row = cur.fetchone()
            if row is None:
                return None
            match_uuid, starts, target, description, pitch, summary_message_id = row
            cur.execute(
                "SELECT display_name, status, team FROM participant "
                "WHERE match_uuid = %s ORDER BY position",
                [match_uuid],
            )
            participants = cur.fetchall()
        starts = starts.astimezone(TIMEZONE)
        teams = None
        if any(team for _, _, team in participants):
            teams = {
                colour: [name for name, _, team in participants if team == colour]
                for colour in ("black", "white")
            }
        return {
            "players": [(name, status == "maybe") for name, status, _ in participants]
            or None,
            "day": format_day(starts),
            "time": format_time(starts),
            "target": target,
            "description": description,
            "pitch": pitch,
            "teams": teams,
            "summary_message_id": summary_message_id,
        }

    def close(self):
        self.conn.close()
