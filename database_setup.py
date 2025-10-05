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
        special_instructions TEXT, -- Optional instructions for the AI
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

    # --- 4. Safely add new columns to existing tables (for migrations) ---
    try:
        # Add the special_instructions column to the plans table if it doesn't exist
        cursor.execute("ALTER TABLE plans ADD COLUMN special_instructions TEXT;")
        print("✅ Added 'special_instructions' column to 'plans' table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            # This is expected if the column already exists, so we can ignore it.
            pass
        else:
            raise e # Raise any other unexpected database errors.

    # Commit changes (save)
    conn.commit()

    # Close the connection
    conn.close()

    print("✅ Database 'learning_os.db' is set up and ready.")

# --- Main Execution Area ---
if __name__ == '__main__':
    setup_database()