import sqlite3
import duckdb
import os

DB_DIR = 'sql'
SQLITE3_DB_PATH = os.path.join(DB_DIR, "test.db")
DUCKDB_PATH = os.path.join(DB_DIR, "test.duckdb")

def setup_dbs():
    """Sets up SQL DBs with tables and data."""
    connection_sqlite3 = sqlite3.connect(SQLITE3_DB_PATH)
    connection_duckdb = duckdb.connect(DUCKDB_PATH)
    cursor_sqlite3 = connection_sqlite3.cursor()
    cursor_duckdb = connection_duckdb.cursor()

    cursor_sqlite3.execute('CREATE TABLE IF NOT EXISTS table1 (column1 INTEGER, column2 INTEGER, column3 INTEGER, column4 INTEGER)')
    cursor_sqlite3.execute('CREATE TABLE IF NOT EXISTS table2 (column1 INTEGER, column2 INTEGER, column3 INTEGER, column4 INTEGER)')
    cursor_sqlite3.execute('CREATE TABLE IF NOT EXISTS table3 (column1 INTEGER, column2 INTEGER, column3 INTEGER, column4 INTEGER)')
    cursor_duckdb.execute('CREATE TABLE IF NOT EXISTS table1 (column1 INTEGER, column2 INTEGER, column3 INTEGER, column4 INTEGER)')
    cursor_duckdb.execute('CREATE TABLE IF NOT EXISTS table2 (column1 INTEGER, column2 INTEGER, column3 INTEGER, column4 INTEGER)')
    cursor_duckdb.execute('CREATE TABLE IF NOT EXISTS table3 (column1 INTEGER, column2 INTEGER, column3 INTEGER, column4 INTEGER)')

    for i in range(1, 6):
        cursor_sqlite3.executemany('INSERT INTO table1 VALUES (?, ?, ?, ?)', [(i, i*2, i*3, i*4)])
        cursor_sqlite3.executemany('INSERT INTO table2 VALUES (?, ?, ?, ?)', [(i, i+1, i+2, i+3)])
        cursor_sqlite3.executemany('INSERT INTO table3 VALUES (?, ?, ?, ?)', [(i*2, i*3, i*4, i*5)])
        cursor_duckdb.executemany('INSERT INTO table1 VALUES (?, ?, ?, ?)', [(i, i*2, i*3, i*4)])
        cursor_duckdb.executemany('INSERT INTO table2 VALUES (?, ?, ?, ?)', [(i, i+1, i+2, i+3)])
        cursor_duckdb.executemany('INSERT INTO table3 VALUES (?, ?, ?, ?)', [(i*2, i*3, i*4, i*5)])

    connection_sqlite3.commit()
    connection_sqlite3.close()
    connection_duckdb.commit()
    connection_duckdb.close()

def execute_query_sqlite3(sql_query):
    """Executes a given SQL query on SQLite3"""
    connection = sqlite3.connect(SQLITE3_DB_PATH)
    cursor = connection.cursor()
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        return results
    except sqlite3.Error as e:
        return f'Error: {e}'
    finally:
        connection.close()

def execute_query_duckdb(sql_query):
    """Executes a given SQL query on DuckDB"""
    connection = duckdb.connect(DUCKDB_PATH)
    try:
        results = connection.execute(sql_query).fetchall()
        return results
    except duckdb.Error as e:
        return f'Error: {e}'
    finally:
        connection.close()

if __name__ == "__main__":
    setup_dbs()