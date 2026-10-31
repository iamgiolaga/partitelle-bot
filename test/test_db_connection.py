"""Connection pool of the db layer: lazy creation, reuse, and a clear error when the database is unreachable."""

import importlib
import logging
import re

import pytest

from db import connection as db_connection


@pytest.fixture
def fresh_pool():
    """Run with no pool and leave none behind, whatever the test did."""
    db_connection.close_pool()
    yield
    db_connection.close_pool()


def test_importing_the_module_does_not_open_a_pool(fresh_pool):
    assert db_connection._pool is None


def test_the_pool_is_created_on_first_use_and_reused(fresh_pool, caplog):
    caplog.set_level(logging.INFO, logger="db.connection")
    with db_connection.connection() as conn:
        assert conn.execute("SELECT 1").fetchone() == (1,)
    pool = db_connection._pool
    assert pool is not None
    with db_connection.connection():
        pass
    assert db_connection._pool is pool
    # the server version is logged once, when the pool is created
    messages = [r.getMessage() for r in caplog.records if r.name == "db.connection"]
    assert len(messages) == 1
    assert re.fullmatch(
        r"PostgreSQL database version: PostgreSQL \d+\.\d+ .+", messages[0]
    )


def test_connections_use_the_configured_schema_and_autocommit(fresh_pool):
    with db_connection.connection() as conn:
        assert conn.autocommit is True
        schema = conn.execute("SHOW search_path").fetchone()[0]
    assert schema == db_connection.db_schema


def test_close_pool_allows_a_new_one_to_be_created(fresh_pool):
    db_connection.get_pool()
    db_connection.close_pool()
    assert db_connection._pool is None
    db_connection.close_pool()
    assert db_connection.get_pool() is db_connection._pool


def test_an_unreachable_database_raises_a_clear_error(fresh_pool, monkeypatch):
    monkeypatch.setattr(db_connection, "port", "1")
    monkeypatch.setattr(db_connection, "POOL_TIMEOUT", 1)
    with pytest.raises(db_connection.DatabaseUnavailable) as error:
        with db_connection.connection():
            pass
    assert "localhost:1" in str(error.value)
    assert db_connection._pool is None


def test_an_exhausted_pool_raises_a_clear_error(fresh_pool, monkeypatch):
    monkeypatch.setattr(db_connection, "POOL_TIMEOUT", 0.2)
    pool = db_connection.get_pool()
    pool.timeout = 0.2
    held = [pool.getconn() for _ in range(db_connection.POOL_MAX_SIZE)]
    try:
        with pytest.raises(db_connection.DatabaseUnavailable):
            with db_connection.connection():
                pass
    finally:
        for conn in held:
            pool.putconn(conn)


def test_an_invalid_schema_is_rejected(fresh_pool, monkeypatch):
    monkeypatch.setattr(db_connection, "db_schema", "bad;schema")
    with pytest.raises(ValueError):
        db_connection.get_pool()


@pytest.mark.parametrize("value", [None, ""])
def test_a_missing_schema_stops_the_startup(monkeypatch, value):
    from conf import conf

    if value is None:
        monkeypatch.delenv("PB_DB_SCHEMA")
    else:
        monkeypatch.setenv("PB_DB_SCHEMA", value)
    try:
        with pytest.raises(RuntimeError, match="PB_DB_SCHEMA is not set"):
            importlib.reload(conf)
    finally:
        monkeypatch.undo()
        importlib.reload(conf)
