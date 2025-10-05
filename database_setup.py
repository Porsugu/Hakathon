# File Name: database_setup.py
import sqlite3

def setup_database():
    """
    Connect to the SQLite database and create the required tables.
    If the database file does not exist, this function will automatically create it.
    """
    # Connect to the database file named learning_os.db
    conn = sqlite3.connect('learning_os.db')

    # Create a cursor object to execute SQL commands
    cursor = conn.cursor()

    # --- 1. Create the users table ---
    # IF NOT EXISTS: If the table already exists, it will not be recreated
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        uid INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    ''')

    # --- 2. Create the plans table ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS plans (
        pid INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER NOT NULL,
        plan_name TEXT NOT NULL,
        daily_content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (uid) REFERENCES users (uid)
    );
    ''')

    # --- 3. Create the knowledge_items table ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS knowledge_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid INTEGER NOT NULL,
        pid INTEGER, -- Optional, allows NULL
        item_type TEXT NOT NULL,
        term TEXT NOT NULL,
        definition TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (uid) REFERENCES users (uid),
        FOREIGN KEY (pid) REFERENCES plans (pid)
    );
    ''')

    # Commit changes (save)
    conn.commit()

    # Close the connection
    conn.close()

    print("Database 'learning_os.db' has been successfully created, and the three tables are ready.")

# --- Main Execution Area ---
if __name__ == '__main__':
    setup_database()