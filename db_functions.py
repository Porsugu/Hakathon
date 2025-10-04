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
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # If the username already exists (UNIQUE constraint failed)
        return False
    finally:
        conn.close()
    return True


def get_user_by_username(username):
    """
    Query user data by username.
    """
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()
    return user


# --- Plan Functions ---

def add_plan(uid, plan_name, daily_content_json):
    """
    Add a learning plan for a specific user.
    """
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO plans (uid, plan_name, daily_content) VALUES (?, ?, ?)",
        (uid, plan_name, daily_content_json)
    )
    conn.commit()
    conn.close()


def get_plans_by_user(uid):
    """
    Query all learning plans for a specific user.
    """
    conn = get_db_connection()
    plans = conn.execute(
        "SELECT * FROM plans WHERE uid = ? ORDER BY created_at DESC",
        (uid,)
    ).fetchall()
    conn.close()
    return plans


def update_plan_content(pid, new_daily_content_json):
    """
    Update the daily content of a specific plan (usually for progress updates).
    """
    conn = get_db_connection()
    conn.execute(
        "UPDATE plans SET daily_content = ? WHERE pid = ?",
        (new_daily_content_json, pid)
    )
    conn.commit()
    conn.close()


def delete_plan(pid):
    """
    Delete a learning plan.
    """
    conn = get_db_connection()
    # Suggestion: Also delete knowledge items related to this plan, or set their pid to NULL
    conn.execute("DELETE FROM plans WHERE pid = ?", (pid,))
    conn.commit()
    conn.close()


# --- Knowledge Item Functions ---

def add_knowledge_item(uid, pid, item_type, term, definition):
    """
    Add a knowledge item. pid can be None.
    """
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO knowledge_items (uid, pid, item_type, term, definition) VALUES (?, ?, ?, ?, ?)",
        (uid, pid, item_type, term, definition)
    )
    conn.commit()
    conn.close()


def get_knowledge_items_by_user(uid):
    """
    Query all knowledge items for a specific user.
    """
    conn = get_db_connection()
    items = conn.execute(
        "SELECT * FROM knowledge_items WHERE uid = ? ORDER BY created_at DESC",
        (uid,)
    ).fetchall()
    conn.close()
    return items


def get_knowledge_items_by_plan(uid, pid):
    """
    Query knowledge items collected under a specific plan for a user.
    """
    conn = get_db_connection()
    items = conn.execute(
        "SELECT * FROM knowledge_items WHERE uid = ? AND pid = ?",
        (uid, pid)
    ).fetchall()
    conn.close()
    return items


def delete_knowledge_item(item_id):
    """
    Delete a knowledge item.
    """
    conn = get_db_connection()
    conn.execute("DELETE FROM knowledge_items WHERE item_id = ?", (item_id,))
    conn.commit()
    conn.close()