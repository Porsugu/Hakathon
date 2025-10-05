# File Name: db_functions.py
import os, sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(BASE_DIR, "learning_os.db")

# DATABASE_FILE = 'learning_os.db'

def get_db_connection():
    """
    Establish and return a database connection.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # Allows returned data to be accessed like a dictionary using column names
    return conn


# --- User Functions ---

def add_user(username, password_hash):
    """
    Add a new user to the users table.
    """
    sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
    with get_db_connection() as conn:
        try:
            conn.execute(sql, (username, password_hash))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # If the username already exists (UNIQUE constraint failed)
            return False


def get_user_by_username(username):
    """
    Query user data by username.
    """
    sql = "SELECT * FROM users WHERE username = ?"
    with get_db_connection() as conn:
        user = conn.execute(sql, (username,)).fetchone()
        return user


# --- Plan Functions ---

def add_plan(uid, plan_name, daily_content_json):
    """
    Add a learning plan for a specific user.
    """
    sql = "INSERT INTO plans (uid, plan_name, daily_content) VALUES (?, ?, ?)"
    with get_db_connection() as conn:
        conn.execute(sql, (uid, plan_name, daily_content_json))
        conn.commit()


def get_plans_by_user(uid):
    """
    Query all learning plans for a specific user.
    """
    sql = "SELECT * FROM plans WHERE uid = ? ORDER BY created_at DESC"
    with get_db_connection() as conn:
        plans = conn.execute(sql, (uid,)).fetchall()
        return plans


def update_plan_content(pid, new_daily_content_json):
    """
    Update the daily content of a specific plan (usually for progress updates).
    """
    sql = "UPDATE plans SET daily_content = ? WHERE pid = ?"
    with get_db_connection() as conn:
        conn.execute(sql, (new_daily_content_json, pid))
        conn.commit()


def delete_plan(uid, pid):
    """
    Delete a learning plan and all associated knowledge items for a specific user.
    """
    delete_plan_sql = "DELETE FROM plans WHERE pid = ? AND uid = ?"
    delete_knowledge_sql = "DELETE FROM knowledge_items WHERE pid = ? AND uid = ?"
    with get_db_connection() as conn:
        conn.execute(delete_plan_sql, (pid, uid))
        conn.execute(delete_knowledge_sql, (pid, uid))
        conn.commit()


# --- Knowledge Item Functions ---

def add_knowledge_item(uid, pid, item_type, term, definition):
    """
    Add a knowledge item. pid can be None.
    """
    sql = "INSERT INTO knowledge_items (uid, pid, item_type, term, definition) VALUES (?, ?, ?, ?, ?)"
    with get_db_connection() as conn:
        conn.execute(sql, (uid, pid, item_type, term, definition))
        conn.commit()


def get_knowledge_items_by_user(uid):
    """
    Query all knowledge items for a specific user.
    """
    sql = "SELECT * FROM knowledge_items WHERE uid = ? ORDER BY created_at DESC"
    with get_db_connection() as conn:
        items = conn.execute(sql, (uid,)).fetchall()
        return items


def get_knowledge_items_by_plan(uid, pid):
    """
    Query knowledge items collected under a specific plan for a user.
    """
    sql = "SELECT * FROM knowledge_items WHERE uid = ? AND pid = ?"
    with get_db_connection() as conn:
        items = conn.execute(sql, (uid, pid)).fetchall()
        return items


def delete_knowledge_item(item_id):
    """
    Delete a knowledge item.
    """
    sql = "DELETE FROM knowledge_items WHERE item_id = ?"
    with get_db_connection() as conn:
        conn.execute(sql, (item_id,))
        conn.commit()

def migrate_users_table_for_google():
    """建立/補齊 users 表欄位 + google_sub 唯一索引（只走 Google 登入）"""
    with get_db_connection() as conn:
        cur = conn.cursor()
        # 建表（若不存在）
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            uid INTEGER PRIMARY KEY AUTOINCREMENT,
            google_sub TEXT,         -- Google 的唯一 id
            email      TEXT,
            name       TEXT,
            picture    TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT
        )
        """)
        # 補欄位（如果之前就有表）
        cur.execute("PRAGMA table_info(users)")
        cols = {r["name"] for r in cur.fetchall()}
        for col, typ in [("google_sub","TEXT"),("email","TEXT"),("name","TEXT"),("picture","TEXT"),("updated_at","TEXT")]:
            if col not in cols:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")

        # ✅ 一定要有唯一索引，未來也能改回 ON CONFLICT 寫法
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_sub
            ON users(google_sub)
        """)
        conn.commit()

def upsert_google_user(info: dict):
    """
    只用 Google 登入：
      - 若 google_sub 已存在：更新 email/name/picture + updated_at，回傳 uid
      - 若不存在：插入新用戶，回傳新 uid
    👉 用「先 UPDATE，沒有再 INSERT」策略，避免你遇到的 ON CONFLICT 版本/索引問題
    """
    sub     = info.get("sub")
    email   = info.get("email")
    name    = info.get("name")
    picture = info.get("picture")
    if not sub:
        raise ValueError("userinfo 缺少 'sub'")

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection() as conn:
        cur = conn.cursor()
        # 1) 先嘗試更新既有用戶
        cur.execute("""
            UPDATE users
               SET email   = COALESCE(?, email),
                   name    = COALESCE(?, name),
                   picture = COALESCE(?, picture),
                   updated_at = ?
             WHERE google_sub = ?
        """, (email, name, picture, now, sub))

        # 2) 若沒更新到任何列 → 插入新用戶
        if cur.rowcount == 0:
            cur.execute("""
                INSERT INTO users (google_sub, email, name, picture, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sub, email, name, picture, now, now))

        conn.commit()
        row = conn.execute("SELECT uid FROM users WHERE google_sub = ?", (sub,)).fetchone()
        return row["uid"] if row else None