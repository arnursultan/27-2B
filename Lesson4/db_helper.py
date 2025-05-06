import sqlite3
from sqlite3 import Error

class DBHelper:
    def __init__(self, db_path='my_database.db'):
        self.db_path = db_path
        self._initialize_db()

    def _connect(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            return conn
        except Error as e:
            print(f"Ошибка подключения к БД: {e}")
            raise

    def _initialize_db(self):
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            name   TEXT    NOT NULL,
            age    INTEGER,
            email  TEXT    UNIQUE
        );
        """
        conn = self._connect()
        try:
            conn.execute(sql)
            conn.commit()
        finally:
            conn.close()

    def add_user(self, name, age, email=None):
        sql = "INSERT INTO users (name, age, email) VALUES (?, ?, ?)"
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (name, age, email))
            conn.commit()
            return cur.lastrowid
        except Error as e:
            print(f"Ошибка при добавлении пользователя: {e}")
            raise
        finally:
            conn.close()

    def get_all_users(self):
        sql = "SELECT * FROM users ORDER BY id"
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql)
            return cur.fetchall()
        finally:
            conn.close()

    def find_users(self, keyword):
        sql = "SELECT * FROM users WHERE name LIKE ? OR email LIKE ?"
        like = f"%{keyword}%"
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (like, like))
            return cur.fetchall()
        finally:
            conn.close()

    def update_user(self, user_id, name=None, age=None, email=None):
        fields = []
        params = []
        if name is not None:
            fields.append("name = ?");   params.append(name)
        if age is not None:
            fields.append("age = ?");    params.append(age)
        if email is not None:
            fields.append("email = ?");  params.append(email)

        if not fields:
            return 0  # нечего обновлять

        params.append(user_id)
        sql = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()

    def delete_user(self, user_id):
        sql = "DELETE FROM users WHERE id = ?"
        conn = self._connect()
        try:
            cur = conn.cursor()
            cur.execute(sql, (user_id,))
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()