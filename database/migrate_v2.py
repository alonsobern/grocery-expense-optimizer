import sqlite3
import os

# Absolute path to the database file
DB_PATH = r"c:\Users\westm\iCloudDrive\Documents\PORTFOLIO\Web Developer\Personal Grocery & Expense Optimizer\database\grocery.db"

def migrate():
    print(f"Connecting to database at: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Error: Database file not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Rename existing products table
        print("Renaming old products table...")
        cursor.execute("ALTER TABLE products RENAME TO products_old")

        # 2. Create new products table with composite uniqueness constraint
        print("Creating new products table with composite constraint (name + category_id)...")
        cursor.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                FOREIGN KEY (category_id) REFERENCES categories (id),
                UNIQUE(name, category_id) -- Allows same name in different categories
            )
        ''')

        # 3. Copy data from old table to new table
        print("Migrating data to new products table...")
        cursor.execute('''
            INSERT INTO products (id, name, category_id)
            SELECT id, name, category_id FROM products_old
        ''')

        # 4. Drop the old table
        print("Removing old products table...")
        cursor.execute("DROP TABLE products_old")

        conn.commit()
        print("Migration v2 completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
