import os

env = os.getenv("ENV", "local")
token = os.getenv("PB_TG_TOKEN")
hosting_url = os.getenv("PB_URL")
host = os.getenv("PB_DB_HOST")
database = os.getenv("PB_DB_NAME")
user = os.getenv("PB_DB_USER")
password = os.getenv("PB_DB_PASSWORD")
port = os.getenv("PB_DB_PORT")
# Postgres schema holding the bot tables: `staging`, `prod`, or `public` (legacy layout, default)
db_schema = os.getenv("PB_DB_SCHEMA") or "public"
# Optional secret for the Telegram webhook; when unset it is derived from the bot token (see main.py)
webhook_secret = os.getenv("PB_WEBHOOK_SECRET")
