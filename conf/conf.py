import os

env = os.getenv('ENV', 'local')
token = os.getenv("PB_TG_TOKEN")
hosting_url = os.getenv("PB_URL")
table_name = os.getenv("PB_DB_TABLE_NAME")
host = os.getenv("PB_DB_HOST")
database = os.getenv("PB_DB_NAME")
user = os.getenv("PB_DB_USER")
password = os.getenv("PB_DB_PASSWORD")
port = os.getenv("PB_DB_PORT")