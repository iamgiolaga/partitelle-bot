import psycopg2
from db.config import config
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
        try:
            params = config()
            conn = psycopg2.connect(**params)
            conn.autocommit = True
            cur = conn.cursor()
            print('PostgreSQL database version:')
            cur.execute('SELECT version()')
            db_version = cur.fetchone()
            print(db_version)
            return cur
        except (Exception, psycopg2.DatabaseError) as error:
            print("There was an issue during the db connection:")
            print(error)