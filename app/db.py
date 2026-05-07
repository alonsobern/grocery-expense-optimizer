import sqlite3
import os
import random
from datetime import datetime, timedelta

# ==========================================
# DATABASE CONNECTION & CONFIGURATION
# ==========================================

def get_db_path():
    """Returns the absolute path to the SQLite database file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'database', 'grocery.db')

def get_db_connection():
    """
    Establishes a connection to the SQLite database.
    """
    db_path = get_db_path()
    
    # Ensure the directory exists (important for Render/Docker)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn

def init_db():
    """
    Initializes the database by creating tables if they don't exist.
    Runs on application startup.
    """
    db_path = get_db_path()
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    schema_path = os.path.join(base_dir, 'database', 'schema.sql')
    
    # 1. Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # 2. Execute schema.sql
    print(f"Initializing database at {db_path}...")
    conn = get_db_connection()
    with open(schema_path, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    
    # 3. Optional: Seed if empty
    seed_if_empty()

def seed_if_empty():
    """Seeds the database with full synthetic demo data if the purchases table is empty."""
    conn = get_db_connection()
    try:
        # Check if we have any purchases. If not, we assume a fresh deploy.
        count = conn.execute('SELECT COUNT(*) FROM purchases').fetchone()[0]
        
        if count == 0:
            print("--- Fresh Deployment Detected ---")
            print("Starting automatic demonstration data seeding...")
            _seed_demo_data(conn)
    except Exception as e:
        print(f"Error during database check/seeding: {e}")
    finally:
        conn.close()

def _seed_demo_data(conn):
    """
    Populates the database with a full set of realistic grocery data.
    Follows correct insertion order to respect foreign keys.
    """
    try:
        # 1. Define Data Sets
        stores_list = ["Whole Foods", "Trader Joe's", "Safeway", "Costco", "Walmart", "Aldi", "Farmers Market"]
        categories_catalog = {
            "Produce": ["Organic Bananas", "Honeycrisp Apples", "Avocados", "Spinach", "Tomatoes"],
            "Dairy": ["Whole Milk", "Large Eggs", "Greek Yogurt", "Cheddar Cheese", "Butter"],
            "Bakery": ["Sourdough Bread", "Bagels", "Croissants", "Chocolate Chip Cookies"],
            "Meat": ["Chicken Breast", "Ground Beef", "Salmon Fillet", "Bacon"],
            "Pantry": ["Olive Oil", "Pasta Sauce", "Spaghetti", "Rice", "Peanut Butter"],
            "Frozen": ["Frozen Pizza", "Ice Cream", "Frozen Veggies", "Waffles"],
            "Household": ["Paper Towels", "Laundry Detergent", "Dish Soap"]
        }

        # 2. Insert Stores
        store_ids = []
        for s in stores_list:
            cursor = conn.execute('INSERT OR IGNORE INTO stores (name) VALUES (?)', (s,))
            # If ignore happened, we need to fetch the existing ID
            if cursor.rowcount == 0:
                res = conn.execute('SELECT id FROM stores WHERE name = ?', (s,)).fetchone()
                store_ids.append(res[0])
            else:
                store_ids.append(cursor.lastrowid)

        # 3. Insert Categories and Products
        product_ids = []
        for cat_name, products in categories_catalog.items():
            # Insert Category
            cursor = conn.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (cat_name,))
            if cursor.rowcount == 0:
                res = conn.execute('SELECT id FROM categories WHERE name = ?', (cat_name,)).fetchone()
                cat_id = res[0]
            else:
                cat_id = cursor.lastrowid
            
            # Insert Products for this Category
            for prod_name in products:
                cursor = conn.execute('INSERT OR IGNORE INTO products (name, category_id) VALUES (?, ?)', 
                                    (prod_name, cat_id))
                if cursor.rowcount == 0:
                    res = conn.execute('SELECT id FROM products WHERE name = ? AND category_id = ?', 
                                     (prod_name, cat_id)).fetchone()
                    product_ids.append(res[0])
                else:
                    product_ids.append(cursor.lastrowid)

        # 4. Insert Purchases (Synthetic History)
        # Generate ~150 purchases across the last 6 months
        print(f"Generating synthetic purchase history...")
        for _ in range(150):
            p_id = random.choice(product_ids)
            s_id = random.choice(store_ids)
            price = round(random.uniform(2.50, 35.00), 2)
            
            # Random date within last 180 days
            days_ago = random.randint(0, 180)
            p_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            conn.execute('''
                INSERT INTO purchases (product_id, store_id, price, purchase_date)
                VALUES (?, ?, ?, ?)
            ''', (p_id, s_id, price, p_date))

        conn.commit()

        # 5. Final Summary Logging
        print("--- Seeding Summary ---")
        print(f"Stores inserted:     {len(stores_list)}")
        print(f"Categories inserted: {len(categories_catalog)}")
        print(f"Products inserted:   {len(product_ids)}")
        print(f"Purchases inserted:  150")
        print("-----------------------")

    except Exception as e:
        conn.rollback()
        print(f"CRITICAL: Demo data seeding failed: {e}")
        raise e



# ==========================================
# STORES
# ==========================================

def get_all_stores():
    """Fetches all stores from the database."""
    conn = get_db_connection()
    stores = conn.execute('SELECT * FROM stores ORDER BY name').fetchall()
    conn.close()
    return stores

def add_store(name):
    """
    Adds a new store to the database.
    Returns (True, None) on success, or (False, error_message) on failure.
    """
    if not name or not name.strip():
        return False, "Store name is required"
    
    clean_name = name.strip()
    conn = get_db_connection()
    try:
        # Check for case-insensitive duplicate manually to provide better error
        existing = conn.execute('SELECT id FROM stores WHERE LOWER(name) = LOWER(?)', (clean_name,)).fetchone()
        if existing:
            return False, "Store already exists"

        conn.execute('INSERT INTO stores (name) VALUES (?)', (clean_name,))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "Store already exists"
    finally:
        conn.close()

def check_store_in_use(store_id):
    """Checks if a store is used in any existing purchases."""
    conn = get_db_connection()
    count = conn.execute('SELECT COUNT(*) FROM purchases WHERE store_id = ?', (store_id,)).fetchone()[0]
    conn.close()
    return count > 0

def delete_store(store_id):
    """Deletes a store from the database."""
    conn = get_db_connection()
    conn.execute('DELETE FROM stores WHERE id = ?', (store_id,))
    conn.commit()
    conn.close()

def update_store(store_id, new_name):
    """
    Updates the name of an existing store.
    Returns (True, None) on success, or (False, error_message) on failure.
    """
    if not new_name or not new_name.strip():
        return False, "Store name is required"
    
    clean_name = new_name.strip()
    conn = get_db_connection()
    try:
        # Check for case-insensitive duplicate (excluding self)
        existing = conn.execute('SELECT id FROM stores WHERE LOWER(name) = LOWER(?) AND id != ?', (clean_name, store_id)).fetchone()
        if existing:
            return False, "Another store with this name already exists"

        conn.execute('UPDATE stores SET name = ? WHERE id = ?', (clean_name, store_id))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "Store name must be unique"
    finally:
        conn.close()


# ==========================================
# CATEGORIES
# ==========================================

def get_all_categories():
    """Fetches all categories from the database."""
    conn = get_db_connection()
    categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
    conn.close()
    return categories

def add_category(name):
    """
    Adds a new category to the database.
    Returns (True, None) on success, or (False, error_message) on failure.
    """
    if not name or not name.strip():
        return False, "Category name is required"
    
    clean_name = name.strip()
    conn = get_db_connection()
    try:
        existing = conn.execute('SELECT id FROM categories WHERE LOWER(name) = LOWER(?)', (clean_name,)).fetchone()
        if existing:
            return False, "Category already exists"

        conn.execute('INSERT INTO categories (name) VALUES (?)', (clean_name,))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "Category already exists"
    finally:
        conn.close()

def check_category_in_use(category_id):
    """Checks if a category is tied to any existing products."""
    conn = get_db_connection()
    count = conn.execute('SELECT COUNT(*) FROM products WHERE category_id = ?', (category_id,)).fetchone()[0]
    conn.close()
    return count > 0

def delete_category(category_id):
    """Deletes a category from the database."""
    conn = get_db_connection()
    conn.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    conn.commit()
    conn.close()

def update_category(category_id, new_name):
    """
    Updates the name of an existing category.
    Returns (True, None) on success, or (False, error_message) on failure.
    """
    if not new_name or not new_name.strip():
        return False, "Category name is required"
    
    clean_name = new_name.strip()
    conn = get_db_connection()
    try:
        existing = conn.execute('SELECT id FROM categories WHERE LOWER(name) = LOWER(?) AND id != ?', (clean_name, category_id)).fetchone()
        if existing:
            return False, "Another category with this name already exists"

        conn.execute('UPDATE categories SET name = ? WHERE id = ?', (clean_name, category_id))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "Category name must be unique"
    finally:
        conn.close()


# ==========================================
# PRODUCTS
# ==========================================

def get_all_products():
    """Fetches all products for simple dropdowns."""
    conn = get_db_connection()
    products = conn.execute('SELECT id, name FROM products ORDER BY name').fetchall()
    conn.close()
    return products

def get_products_with_categories():
    """Fetches all products along with their associated category names."""
    conn = get_db_connection()
    products = conn.execute('''
        SELECT p.id, p.name, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.name
    ''').fetchall()
    conn.close()
    return products

def add_product(name, category_id):
    """
    Adds a new product to the database.
    Returns (True, None) on success, or (False, error_message) on failure.
    """
    if not name or not name.strip():
        return False, "Product name is required"
    if not category_id:
        return False, "Category is required"
        
    clean_name = name.strip()
    conn = get_db_connection()
    try:
        # Check for duplicate name WITHIN the same category (case-insensitive)
        existing = conn.execute('SELECT id FROM products WHERE LOWER(name) = LOWER(?) AND category_id = ?', 
                                (clean_name, category_id)).fetchone()
        if existing:
            return False, "Product already exists in this category"

        conn.execute('INSERT INTO products (name, category_id) VALUES (?, ?)',
                     (clean_name, category_id))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError as e:
        if "NOT NULL" in str(e):
            return False, "Category is required"
        return False, "Product already exists in this category"
    finally:
        conn.close()

def check_product_in_use(product_id):
    """Checks if a product is tied to any existing purchases."""
    conn = get_db_connection()
    count = conn.execute('SELECT COUNT(*) FROM purchases WHERE product_id = ?', (product_id,)).fetchone()[0]
    conn.close()
    return count > 0

def delete_product(product_id):
    """Deletes a product from the database."""
    conn = get_db_connection()
    conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()

def update_product(product_id, name, category_id):
    """
    Updates the name and category of an existing product.
    Returns (True, None) on success, or (False, error_message) on failure.
    """
    if not name or not name.strip():
        return False, "Product name is required"
    if not category_id:
        return False, "Category is required"

    clean_name = name.strip()
    conn = get_db_connection()
    try:
        # Check for duplicate name WITHIN the same category, excluding the current product ID
        existing = conn.execute('SELECT id FROM products WHERE LOWER(name) = LOWER(?) AND category_id = ? AND id != ?', 
                                (clean_name, category_id, product_id)).fetchone()
        if existing:
            return False, "Product already exists in this category"

        conn.execute('UPDATE products SET name = ?, category_id = ? WHERE id = ?', (clean_name, category_id, product_id))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "Product already exists in this category"
    finally:
        conn.close()


# ==========================================
# PURCHASES
# ==========================================

def get_purchases_with_details():
    """
    Fetches all purchases with full outer details (Product Name, Category Name, Store Name).
    """
    conn = get_db_connection()
    purchases = conn.execute('''
        SELECT 
            p.id, 
            p.product_id,
            p.store_id,
            prod.name as product_name, 
            cat.name as category_name,
            s.name as store_name,
            p.price,
            p.purchase_date
        FROM purchases p
        JOIN products prod ON p.product_id = prod.id
        LEFT JOIN categories cat ON prod.category_id = cat.id
        LEFT JOIN stores s ON p.store_id = s.id
        ORDER BY p.purchase_date DESC, p.id DESC
    ''').fetchall()
    conn.close()
    return purchases

def add_purchase(product_id, store_id, price, purchase_date):
    """
    Adds a new purchase record.
    Returns (True, None) on success, or (False, error_message) on failure.
    """
    if not product_id:
        return False, "Product is required"
    if not store_id:
        return False, "Store is required"
    try:
        price_val = float(price)
        if price_val <= 0:
            return False, "Price must be greater than 0"
    except (ValueError, TypeError):
        return False, "Invalid price format"

    date_val = purchase_date if purchase_date else datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO purchases (product_id, store_id, price, purchase_date) VALUES (?, ?, ?, ?)',
            (product_id, store_id, price_val, date_val)
        )
        conn.commit()
        return True, None
    except sqlite3.IntegrityError as e:
        return False, f"Integrity Error: {str(e)}"
    finally:
        conn.close()

def delete_purchase(purchase_id):
    """Deletes a purchase log from the database."""
    conn = get_db_connection()
    conn.execute('DELETE FROM purchases WHERE id = ?', (purchase_id,))
    conn.commit()
    conn.close()

def update_purchase(purchase_id, product_id, store_id, price, purchase_date):
    """
    Updates the details of an existing purchase record.
    Returns (True, None) on success, or (False, error_message) on failure.
    """
    if not product_id:
        return False, "Product is required"
    if not store_id:
        return False, "Store is required"
    try:
        price_val = float(price)
        if price_val <= 0:
            return False, "Price must be greater than 0"
    except (ValueError, TypeError):
        return False, "Invalid price format"

    conn = get_db_connection()
    try:
        conn.execute('''
            UPDATE purchases 
            SET product_id = ?, store_id = ?, price = ?, purchase_date = ?
            WHERE id = ?
        ''', (product_id, store_id, price_val, purchase_date, purchase_id))
        conn.commit()
        return True, None
    except sqlite3.Error as e:
        return False, f"Update failed: {str(e)}"
    finally:
        conn.close()
