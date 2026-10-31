import os

env = os.getenv("ENV", "local")
token = os.getenv("PB_TG_TOKEN")
hosting_url = os.getenv("PB_URL")
host = os.getenv("PB_DB_HOST")
database = os.getenv("PB_DB_NAME")
user = os.getenv("PB_DB_USER")
password = os.getenv("PB_DB_PASSWORD")
port = os.getenv("PB_DB_PORT")
# Postgres schema holding the bot tables (`staging` or `prod`). There is no default: the tables exist only in
# that schema, so a missing value must stop the bot at startup instead of failing on the first message.
db_schema = os.getenv("PB_DB_SCHEMA")
if not db_schema:
    raise RuntimeError(
        "PB_DB_SCHEMA is not set: set it to the Postgres schema of this environment (e.g. 'prod' or 'staging')"
    )
# Optional secret for the Telegram webhook; when unset it is derived from the bot token (see main.py)
webhook_secret = os.getenv("PB_WEBHOOK_SECRET")
