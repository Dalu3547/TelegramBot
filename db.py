import sqlite3
from api.kaspi import KaspiParser
from api.intertop import IntertopParser
from api.wildberries import WildberriesParser

# Initialize DB and create table if not exists
def init_db():
    conn = sqlite3.connect("products.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tracked_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            source TEXT,
            url TEXT,
            price REAL
        )
    """)
    conn.commit()
    conn.close()

def add_product(user_id, source, url, price):
    if price is None:
        print(f"Skipping DB insert for {url} because price is None")
        return

    conn = sqlite3.connect("products.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tracked_products (user_id, source, url, price)
        VALUES (?, ?, ?, ?)
    """, (user_id, source, url, price))
    conn.commit()
    conn.close()
    print(f"✅ Added to DB: {url} with price {price}")


# Get all products
def get_all_products():
    conn = sqlite3.connect("products.db")
    cur = conn.cursor()
    cur.execute("SELECT user_id, source, url, price FROM tracked_products")
    products = cur.fetchall()
    conn.close()
    return products

# Update product price
def update_product_price(url, new_price):
    conn = sqlite3.connect("products.db")
    cur = conn.cursor()
    cur.execute("UPDATE tracked_products SET price = ? WHERE url = ?", (new_price, url))
    conn.commit()
    conn.close()
