import sqlite3
import os

DATABASE = 'database/grocery.db'
SCHEMA = 'database/schema.sql'

def init_db():
    try:
        # Ensure database directory exists
        os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
        
        conn = sqlite3.connect(DATABASE)
        with open(SCHEMA, 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    init_db()
