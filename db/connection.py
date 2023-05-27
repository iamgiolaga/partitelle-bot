import psycopg2
from db.config import config

def connect():
    conn = None
    try:
        params = config()
        conn = psycopg2.connect(**params)
        conn.autocommit = True
        cur = conn.cursor()
        return cur
    except (Exception, psycopg2.DatabaseError) as error:
        print("There was an issue during the db connection:")
        print(error)
    finally:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
