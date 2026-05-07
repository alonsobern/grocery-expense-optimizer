import sqlite3
import os

DATABASE = 'database/grocery.db'

def migrate():
    if not os.path.exists(DATABASE):
        print("Database does not exist. Please run init_db.py first.")
        return

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("Starting migration...")

    try:
        # 1. Ensure we have at least one Category and one Store for defaults
        cursor.execute("INSERT OR IGNORE INTO categories (name) VALUES ('General')")
        cursor.execute("SELECT id FROM categories WHERE name = 'General'")
        default_cat_id = cursor.fetchone()['id']

        cursor.execute("INSERT OR IGNORE INTO stores (name) VALUES ('General')")
        cursor.execute("SELECT id FROM stores WHERE name = 'General'")
        default_store_id = cursor.fetchone()['id']

        # 2. Fix NULL category_id in products
        cursor.execute("UPDATE products SET category_id = ? WHERE category_id IS NULL", (default_cat_id,))
        
        # 3. Fix NULL store_id in purchases
        cursor.execute("UPDATE purchases SET store_id = ? WHERE store_id IS NULL", (default_store_id,))

        # 4. Handle Duplicate Products (Case-insensitive)
        # We find duplicates, keep the oldest one, and point all purchases to it.
        cursor.execute("SELECT name, COUNT(*) as count FROM products GROUP BY LOWER(name) HAVING count > 1")
        duplicates = cursor.fetchall()
        for dup in duplicates:
            name_lower = dup['name'].lower()
            cursor.execute("SELECT id FROM products WHERE LOWER(name) = ? ORDER BY id ASC", (name_lower,))
            ids = [row['id'] for row in cursor.fetchall()]
            primary_id = ids[0]
            redundant_ids = ids[1:]
            
            print(f"Merging duplicates for '{dup['name']}': Keeping ID {primary_id}, removing IDs {redundant_ids}")
            for rid in redundant_ids:
                cursor.execute("UPDATE purchases SET product_id = ? WHERE product_id = ?", (primary_id, rid))
                cursor.execute("DELETE FROM products WHERE id = ?", (rid,))

        # 5. Recreate Tables with new constraints
        # SQLite doesn't support ALTER TABLE for constraints, so we use the temp table pattern.
        
        # Products Table
        cursor.execute("CREATE TABLE products_new (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, category_id INTEGER NOT NULL, FOREIGN KEY (category_id) REFERENCES categories (id))")
        cursor.execute("INSERT INTO products_new (id, name, category_id) SELECT id, name, category_id FROM products")
        
        # Purchases Table
        cursor.execute("CREATE TABLE purchases_new (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL, store_id INTEGER NOT NULL, price REAL NOT NULL CHECK(price > 0), purchase_date TEXT DEFAULT CURRENT_DATE, FOREIGN KEY (product_id) REFERENCES products (id), FOREIGN KEY (store_id) REFERENCES stores (id))")
        cursor.execute("INSERT INTO purchases_new (id, product_id, store_id, price, purchase_date) SELECT id, product_id, store_id, price, purchase_date FROM purchases")

        # 6. Replace old tables
        cursor.execute("DROP TABLE purchases")
        cursor.execute("DROP TABLE products")
        cursor.execute("ALTER TABLE products_new RENAME TO products")
        cursor.execute("ALTER TABLE purchases_new RENAME TO purchases")

        conn.commit()
        print("Migration completed successfully.")

    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
