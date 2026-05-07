import sqlite3
import os
import random
from datetime import datetime, timedelta

# ==========================================================
# CONFIGURATION
# ==========================================================

# Path to the database file
BASE_DIR = r"c:\Users\westm\iCloudDrive\Documents\PORTFOLIO\Web Developer\Personal Grocery & Expense Optimizer"
DB_PATH = os.path.join(BASE_DIR, 'database', 'grocery.db')

# Seeding Parameters
NUM_PURCHASES = 250
DAYS_BACK = 180  # ~6 months

# ==========================================================
# DATA SETS
# ==========================================================

STORES = [
    "Whole Foods Market", "Trader Joe's", "Safeway", "Kroger", 
    "Costco", "Walmart Supercenter", "Target", "Aldi", 
    "Farmers Market", "Local Co-op"
]

CATEGORIES = [
    "Produce (Fruits & Veggies)", "Dairy & Eggs", "Bakery", 
    "Meat & Seafood", "Pantry Essentials", "Frozen Foods", 
    "Beverages", "Snacks", "Household & Cleaning", 
    "Personal Care", "Deli & Prepared Foods"
]

# Mapping Products to Categories
PRODUCT_CATALOG = {
    "Produce (Fruits & Veggies)": [
        "Organic Bananas", "Honeycrisp Apples", "Avocados", "Baby Spinach", 
        "Roma Tomatoes", "Seedless Grapes", "Blueberries", "Broccoli Crowns"
    ],
    "Dairy & Eggs": [
        "Whole Milk", "Large Grade A Eggs", "Unsalted Butter", "Greek Yogurt", 
        "Cheddar Cheese Block", "Almond Milk", "Sour Cream"
    ],
    "Bakery": [
        "Sourdough Bread", "Whole Wheat Loaf", "Bagels", "Chocolate Chip Cookies", 
        "Croissants", "Tortillas"
    ],
    "Meat & Seafood": [
        "Chicken Breast", "Ground Beef (80/20)", "Salmon Fillet", "Bacon", 
        "Pork Chops", "Shrimp"
    ],
    "Pantry Essentials": [
        "Olive Oil", "White Rice", "Pasta Sauce", "Spaghetti", 
        "Peanut Butter", "Canned Black Beans", "All-Purpose Flour"
    ],
    "Frozen Foods": [
        "Frozen Pizza", "Mixed Vegetables", "Ice Cream (Vanilla)", 
        "Frozen Waffles", "Fruit Medley (for Smoothies)"
    ],
    "Beverages": [
        "Sparkling Water", "Coffee Beans", "Orange Juice", "Green Tea Bags", 
        "Cola 12-Pack"
    ],
    "Snacks": [
        "Potato Chips", "Mixed Nuts", "Granola Bars", "Hummus", "Pretzels"
    ],
    "Household & Cleaning": [
        "Paper Towels", "Laundry Detergent", "Dish Soap", "Trash Bags"
    ],
    "Personal Care": [
        "Toothpaste", "Shampoo", "Hand Soap", "Body Wash"
    ],
    "Deli & Prepared Foods": [
        "Rotisserie Chicken", "Potato Salad", "Sliced Turkey Breast", "Olives"
    ]
}

# ==========================================================
# SEEDING LOGIC
# ==========================================================

def seed_database():
    print(f"Starting database seeding at: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("Error: Database file not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # 1. Clear existing data
        print("Clearing existing data...")
        cursor.execute("PRAGMA foreign_keys = OFF;")
        cursor.execute("DELETE FROM purchases")
        cursor.execute("DELETE FROM products")
        cursor.execute("DELETE FROM categories")
        cursor.execute("DELETE FROM stores")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('purchases', 'products', 'categories', 'stores')")
        cursor.execute("PRAGMA foreign_keys = ON;")

        # 2. Seed Stores
        print("Seeding Stores...")
        for store in STORES:
            cursor.execute("INSERT INTO stores (name) VALUES (?)", (store,))
        
        # 3. Seed Categories
        print("Seeding Categories...")
        for category in CATEGORIES:
            cursor.execute("INSERT INTO categories (name) VALUES (?)", (category,))

        # Fetch IDs
        cursor.execute("SELECT id, name FROM categories")
        category_map = {name: cid for cid, name in cursor.fetchall()}
        
        cursor.execute("SELECT id FROM stores")
        store_ids = [row[0] for row in cursor.fetchall()]

        # 4. Seed Products
        print("Seeding Products...")
        product_ids = []
        for cat_name, products in PRODUCT_CATALOG.items():
            cat_id = category_map[cat_name]
            for prod_name in products:
                cursor.execute("INSERT INTO products (name, category_id) VALUES (?, ?)", (prod_name, cat_id))
                product_ids.append(cursor.lastrowid)

        # 5. Seed Purchases
        print(f"Seeding {NUM_PURCHASES} Purchases...")
        for _ in range(NUM_PURCHASES):
            product_id = random.choice(product_ids)
            store_id = random.choice(store_ids)
            
            # Generate realistic price between $1.50 and $45.00
            price = round(random.uniform(1.50, 45.00), 2)
            
            # Generate random date in the last 6 months
            random_days = random.randint(0, DAYS_BACK)
            purchase_date = (datetime.now() - timedelta(days=random_days)).strftime('%Y-%m-%d')
            
            cursor.execute('''
                INSERT INTO purchases (product_id, store_id, price, purchase_date)
                VALUES (?, ?, ?, ?)
            ''', (product_id, store_id, price, purchase_date))

        conn.commit()
        
        # Summary
        print("\n" + "="*30)
        print("SEEDING COMPLETE")
        print("="*30)
        
        cursor.execute("SELECT COUNT(*) FROM stores")
        print(f"Stores:     {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM categories")
        print(f"Categories: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM products")
        print(f"Products:   {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM purchases")
        print(f"Purchases:  {cursor.fetchone()[0]}")
        print("="*30 + "\n")

    except Exception as e:
        conn.rollback()
        print(f"Seeding failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    seed_database()
