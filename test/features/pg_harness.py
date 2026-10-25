"""Real-Postgres support for the feature tests (harness only: the .feature files never see any of this)."""

import json
import os

import psycopg
import pytest
from psycopg import sql

_MAYBE_MARKER = "%is%maybe%present"  # how a "maybe" player is persisted


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
        self.table = os.environ["PB_DB_TABLE_NAME"]

    def truncate(self):
        with self.conn.cursor() as cur:
            cur.execute(sql.SQL("TRUNCATE {}").format(sql.Identifier(self.table)))

    def _set(self, chat_id, column, value):
        with self.conn.cursor() as cur:
            cur.execute(
                sql.SQL("UPDATE {} SET {} = %s WHERE chat_id = %s").format(
                    sql.Identifier(self.table), sql.Identifier(column)
                ),
                [value, chat_id],
            )

    def set_target(self, chat_id, target):
        self._set(chat_id, "target", target)

    def set_time(self, chat_id, time):
        self._set(chat_id, "time", time)

    def set_pitch(self, chat_id, pitch):
        self._set(chat_id, "pitch", pitch)

    def set_players(self, chat_id, players):
        """`players` is a list of (name, is_maybe), in order."""
        self._set(
            chat_id,
            "players",
            [name + _MAYBE_MARKER if is_maybe else name for name, is_maybe in players],
        )

    def set_teams(self, chat_id, black, white):
        self._set(chat_id, "teams", json.dumps({"black": black, "white": white}))

    def fetch_match(self, chat_id):
        """The persisted match of a chat as a dict of test values, or None when there is none.

        players: None when never set, else a list of (name, is_maybe); teams: None or {"black": [...],
        "white": [...]} (key order as persisted).
        """
        with self.conn.cursor() as cur:
            cur.execute(
                sql.SQL(
                    "SELECT players, day, time, target, custom_message, pitch, teams, "
                    "bot_last_message_id FROM {} WHERE chat_id = %s"
                ).format(sql.Identifier(self.table)),
                [chat_id],
            )
            row = cur.fetchone()
        if row is None:
            return None
        keys = (
            "players",
            "day",
            "time",
            "target",
            "description",
            "pitch",
            "teams",
            "summary_message_id",
        )
        match = dict(zip(keys, row))
        if match["players"] is not None:
            match["players"] = [
                (p[: -len(_MAYBE_MARKER)], True)
                if p.endswith(_MAYBE_MARKER)
                else (p, False)
                for p in match["players"]
            ]
        return match

    def close(self):
        self.conn.close()
