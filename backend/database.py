import sqlite3
from sqlite3 import Error


def create_connection(db_file='reference.db'):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn


def delete_papers_table():
    create_table_sql = "DROP TABLE papers"
    conn = create_connection()
    c = conn.cursor()
    c.execute(create_table_sql)
    conn.close()


def create_papers_table():
    conn = create_connection()
    create_table_sql = """CREATE TABLE papers (
                                        id integer PRIMARY KEY,
                                        filename text NOT NULL,
                                        oauth_token text,
                                        title text,
                                        authors text,
                                        venue text,
                                        year text
                                    ); """
    c = conn.cursor()
    c.execute(create_table_sql)

    if conn:
        conn.close()