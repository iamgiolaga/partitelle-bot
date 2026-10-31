"""Apply the pending yoyo migrations to the schema selected by PB_DB_SCHEMA.

Usage: python -m db.migrate
"""

from pathlib import Path
from urllib.parse import quote

import psycopg
from psycopg import sql
from yoyo import get_backend, read_migrations

from conf.conf import host, database, user, password, port, db_schema
from db.connection import validate_schema

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def build_uri(schema):
    # `schema` is handled by yoyo's postgres backend: it runs `SET search_path TO <schema>`
    # on every connection, so also yoyo's own tables (_yoyo_migration, ...) live in the schema.
    return (
        f"postgresql+psycopg://{quote(user or '', safe='')}:{quote(password or '', safe='')}"
        f"@{host}:{port or 5432}/{database}?schema={schema}"
    )


def create_schema(schema):
    with psycopg.connect(
        host=host,
        dbname=database,
        user=user,
        password=password,
        port=port,
        autocommit=True,
    ) as conn:
        conn.execute(
            sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema))
        )


def migrate():
    schema = validate_schema(db_schema)

    # the schema must exist before yoyo connects: it creates its bookkeeping tables on the first connection
    create_schema(schema)
    backend = get_backend(build_uri(schema))

    migrations = read_migrations(str(MIGRATIONS_DIR))
    with backend.lock():
        pending = backend.to_apply(migrations)
        if not pending:
            print(f"Schema '{schema}' is up to date: no migrations to apply")
            return
        print(f"Applying to schema '{schema}': {[m.id for m in pending]}")
        backend.apply_migrations(pending)
        print("Migrations applied")


if __name__ == "__main__":
    migrate()
