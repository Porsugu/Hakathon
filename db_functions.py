# File Name: db_functions.py
import sqlite3

DATABASE_FILE = 'learning_os.db'

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