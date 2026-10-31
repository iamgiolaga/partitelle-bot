"""Top-level test configuration.

`conf.conf` reads the environment at import time and `db.connection` builds its pool lazily from them, so the
environment MUST be in place before any application module is imported. pytest imports this conftest
before collecting anything, which makes it the right (and only) place to do it.

Every value can be overridden with a real environment variable (e.g. in CI).
"""

import os

TEST_ENV_DEFAULTS = {
    "ENV": "local",
    "PB_TG_TOKEN": "123456:TEST",  # dummy: the fake bot never talks to Telegram
    "PB_URL": "http://localhost",
    "PB_DB_HOST": "localhost",
    "PB_DB_PORT": "5432",
    "PB_DB_USER": "partitelle",
    "PB_DB_PASSWORD": "partitelle",
    "PB_DB_NAME": "partitelle_test",
    "PB_DB_SCHEMA": "staging",  # mirrors prod: the schema is built by the real migrations
}

for _key, _value in TEST_ENV_DEFAULTS.items():
    os.environ.setdefault(_key, _value)
