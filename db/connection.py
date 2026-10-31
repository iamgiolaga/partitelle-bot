import atexit
import logging
import re
import threading
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager

from psycopg import Connection, OperationalError
from psycopg_pool import ConnectionPool, PoolTimeout

from conf.conf import host, database, user, password, port, db_schema

logger = logging.getLogger(__name__)

SCHEMA_NAME_RE = re.compile(r"^[a-z_][a-z0-9_]*$")

POOL_MIN_SIZE = 1
POOL_MAX_SIZE = 4
CONNECT_TIMEOUT = 10  # seconds, for a single connection attempt
POOL_TIMEOUT = 10  # seconds, to wait for a free connection / for the pool to open

_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()


class DatabaseUnavailable(Exception):
    """The database cannot be reached (wrong host/credentials, server down, pool exhausted)."""


def validate_schema(schema: str | None) -> str:
    name = schema or ""
    if not SCHEMA_NAME_RE.match(name):
        raise ValueError(
            f"Invalid PB_DB_SCHEMA {schema!r}: it must match {SCHEMA_NAME_RE.pattern}"
        )
    return name


def _unavailable(error: Exception) -> DatabaseUnavailable:
    return DatabaseUnavailable(
        f"Cannot connect to the database {database!r} on {host}:{port or 5432}: {error}"
    )


def _create_pool() -> ConnectionPool:
    schema = validate_schema(db_schema)
    pool = ConnectionPool(
        min_size=POOL_MIN_SIZE,
        max_size=POOL_MAX_SIZE,
        timeout=POOL_TIMEOUT,
        # drop connections closed by the server (e.g. idle timeouts) before handing them out
        check=ConnectionPool.check_connection,
        open=False,
        kwargs={
            "host": host,
            "dbname": database,
            "user": user,
            "password": password,
            "port": port,
            "options": f"-c search_path={schema}",
            "connect_timeout": CONNECT_TIMEOUT,
            # every statement is committed on its own, as it always was
            "autocommit": True,
        },
    )
    try:
        pool.open(wait=True, timeout=POOL_TIMEOUT)
    except PoolTimeout as error:
        pool.close()
        raise _unavailable(error) from error
    try:
        with pool.connection() as conn:
            row = conn.execute("SELECT version()").fetchone()
            version = row[0] if row else None
        logger.info("PostgreSQL database version: %s", version)
    except (PoolTimeout, OperationalError) as error:
        pool.close()
        raise _unavailable(error) from error
    return pool


def get_pool() -> ConnectionPool:
    """The shared connection pool, created and opened on first use (never at import time)."""
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = _create_pool()
        return _pool


def close_pool() -> None:
    global _pool
    with _pool_lock:
        pool, _pool = _pool, None
    if pool is not None:
        pool.close()


atexit.register(close_pool)


@contextmanager
def connection() -> Iterator[Connection]:
    """Check a (autocommit) connection out of the pool for the duration of the block."""
    pool = get_pool()
    with ExitStack() as stack:
        try:
            conn = stack.enter_context(pool.connection())
        except (PoolTimeout, OperationalError) as error:
            raise _unavailable(error) from error
        yield conn
