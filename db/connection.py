import psycopg2
from conf.conf import host, database, user, password, port
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
            conn = psycopg2.connect(**{
                'host': host,
                'database': database,
                'user': user,
                'password': password,
                'port': port
            })
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