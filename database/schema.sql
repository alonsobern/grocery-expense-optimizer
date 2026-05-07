-- Database Schema for Grocery App
-- Version: 1.1 (Strong Validation)

-- Stores Table
CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Categories Table
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Products Table
-- category_id is now NOT NULL to ensure every product is categorized.
-- We use a composite UNIQUE constraint (name, category_id) to allow the same 
-- product name to exist in different categories (e.g. Apple in Fruits vs Apple in Frozen).
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories (id),
    UNIQUE(name, category_id)
);

-- Purchases Table
-- store_id is now NOT NULL to ensure every purchase has a location.
-- price is now constrained to be greater than 0.
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    store_id INTEGER NOT NULL,
    price REAL NOT NULL CHECK(price > 0),
    purchase_date TEXT DEFAULT CURRENT_DATE,
    FOREIGN KEY (product_id) REFERENCES products (id),
    FOREIGN KEY (store_id) REFERENCES stores (id)
);
