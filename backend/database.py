import sqlite3
import os
from config import DATABASE_PATH, BASE_DIR

def get_db():
    """Returns a SQLite connection with row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Initializes tables from schema.sql and seeds initial data if empty."""
    schema_path = os.path.join(BASE_DIR, "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_db()
    cursor = conn.cursor()
    cursor.executescript(schema_sql)

    # Ensure password column exists on demo_profiles if table was already created
    cursor.execute("PRAGMA table_info(demo_profiles)")
    cols = [row["name"] for row in cursor.fetchall()]
    if "password" not in cols:
        cursor.execute("ALTER TABLE demo_profiles ADD COLUMN password TEXT")

    conn.commit()
    conn.close()

def query_db(query, args=(), one=False):
    """Convenience helper to query database and return dictionary objects."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.close()
    if rv:
        if one:
            return dict(rv[0])
        return [dict(row) for row in rv]
    return None if one else []

def execute_db(query, args=()):
    """Convenience helper to execute insert/update/delete and return lastrowid / rowcount."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    last_id = cur.lastrowid
    row_count = cur.rowcount
    conn.close()
    return last_id, row_count
