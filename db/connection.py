import psycopg2
from config import config

""" Connect to the PostgreSQL database server """
def connect():
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        conn.autocommit = True
        cur = conn.cursor()
        return cur
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
