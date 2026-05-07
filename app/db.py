import sqlite3
import os
from datetime import datetime, timedelta

# ==========================================
# DATABASE CONNECTION & CONFIGURATION
# ==========================================

def get_db_connection():
    """
    Establishes a connection to the SQLite database.
    
    Returns:
        sqlite3.Connection: A connection object to the database.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(base_dir, 'database', 'grocery.db')
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Enable foreign key constraints (disabled by default in SQLite)
    # Required to enforce relationships between tables (e.g. Products -> Categories)
    conn.execute('PRAGMA foreign_keys = ON;')
    
    return conn


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
