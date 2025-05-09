import sqlite3

DB_PATH = "users.db"

def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT UNIQUE,
            phone TEXT
        )   
    """)
    conn.commit()
    conn.close()

def update_user(user_id, name, age, email):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET name = ?, age = ?, email = ?
        WHERE id = ?
    """, (name, age, email, user_id))
    conn.commit()
    updated = cursor.rowcount
    conn.close()
    return updated