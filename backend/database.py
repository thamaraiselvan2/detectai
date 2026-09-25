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

    cursor.execute("PRAGMA table_info(trusted_devices)")
    trusted_device_cols = [row["name"] for row in cursor.fetchall()]
    if "account_id" not in trusted_device_cols:
        cursor.execute("ALTER TABLE trusted_devices ADD COLUMN account_id INTEGER")

    cursor.execute("PRAGMA table_info(login_history)")
    login_history_cols = [row["name"] for row in cursor.fetchall()]
    if "account_id" not in login_history_cols:
        cursor.execute("ALTER TABLE login_history ADD COLUMN account_id INTEGER")
    if "registered_email" not in login_history_cols:
        cursor.execute("ALTER TABLE login_history ADD COLUMN registered_email TEXT")
    if "verification_expires_at" not in login_history_cols:
        cursor.execute("ALTER TABLE login_history ADD COLUMN verification_expires_at DATETIME")
    if "authorization_status" not in login_history_cols:
        cursor.execute("ALTER TABLE login_history ADD COLUMN authorization_status TEXT DEFAULT 'PENDING'")
    if "authorization_used_at" not in login_history_cols:
        cursor.execute("ALTER TABLE login_history ADD COLUMN authorization_used_at DATETIME")

    cursor.execute("PRAGMA table_info(alerts)")
    alert_cols = [row["name"] for row in cursor.fetchall()]
    alert_migrations = {
        "alert_type": "TEXT NOT NULL DEFAULT 'impersonation'",
        "classification": "TEXT NOT NULL DEFAULT 'FAKE'",
        "evidence_json": "TEXT",
        "email_status": "TEXT DEFAULT 'skipped'",
        "email_sent_at": "DATETIME",
    }
    for column, definition in alert_migrations.items():
        if column not in alert_cols:
            cursor.execute(f"ALTER TABLE alerts ADD COLUMN {column} {definition}")

    # Remove the legacy email uniqueness constraint while retaining username uniqueness.
    cursor.execute("PRAGMA index_list(registered_profiles)")
    has_unique_email_index = False
    for index_row in cursor.fetchall():
        if not index_row[2]:
            continue
        cursor.execute(f'PRAGMA index_info("{index_row[1]}")')
        index_columns = [column_row[2] for column_row in cursor.fetchall()]
        if index_columns == ["email"]:
            has_unique_email_index = True
            break

    if has_unique_email_index:
        conn.commit()
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("""
            CREATE TABLE registered_profiles_without_email_unique (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT NOT NULL,
                original_profile_id INTEGER NOT NULL,
                registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(original_profile_id) REFERENCES demo_profiles(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            INSERT INTO registered_profiles_without_email_unique
                (id, username, email, original_profile_id, registered_at)
            SELECT id, username, email, original_profile_id, registered_at
            FROM registered_profiles
        """)
        cursor.execute("DROP TABLE registered_profiles")
        cursor.execute("ALTER TABLE registered_profiles_without_email_unique RENAME TO registered_profiles")
        cursor.execute("PRAGMA foreign_keys = ON")

    # Migrate legacy protected registrations into the operational registry.
    cursor.execute("""
        INSERT OR IGNORE INTO protected_profiles
            (username, display_name, email, bio, avatar_url, follower_count, is_monitoring_active)
        SELECT d.username, d.display_name, r.email, d.bio, d.avatar_url,
               d.followers_count, 1
        FROM registered_profiles r
        JOIN demo_profiles d ON d.id = r.original_profile_id
        WHERE NOT EXISTS (
            SELECT 1 FROM protected_profiles p
            WHERE LOWER(p.username) = LOWER(r.username)
        )
    """)

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
