import re

import psycopg2
from conf.conf import host, database, user, password, port, db_schema

SCHEMA_NAME_RE = re.compile(r"^[a-z_][a-z0-9_]*$")


def validate_schema(schema):
    if not SCHEMA_NAME_RE.match(schema or ""):
        raise ValueError(
            f"Invalid PB_DB_SCHEMA {schema!r}: it must match {SCHEMA_NAME_RE.pattern}"
        )
    return schema


class Connection:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.cursor = self.connect()

    def connect(self):
        conn = None
        schema = validate_schema(db_schema)
        try:
            conn = psycopg2.connect(
                **{
                    "host": host,
                    "database": database,
                    "user": user,
                    "password": password,
                    "port": port,
                    "options": f"-c search_path={schema}",
                }
            )
            conn.autocommit = True
            cur = conn.cursor()
            print("PostgreSQL database version:")
            cur.execute("SELECT version()")
            db_version = cur.fetchone()
            print(db_version)
            return cur
        except (Exception, psycopg2.DatabaseError) as error:
            print("There was an issue during the db connection:")
            print(error)
