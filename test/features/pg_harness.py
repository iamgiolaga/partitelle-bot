"""Real-Postgres support for the feature tests (harness only: the .feature files never see any of this)."""

import os

import psycopg2
import pytest
from psycopg2 import sql



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
    conn = psycopg2.connect(connect_timeout=5, **_params(database), **options)
    conn.autocommit = True
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
    except psycopg2.OperationalError as error:
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

    def fetch_match(self, chat_id):
        """The persisted match of a chat as a dict, or None when there is none."""
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
        return dict(zip(keys, row))

    def close(self):
        self.conn.close()
