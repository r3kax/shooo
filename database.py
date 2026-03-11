import sqlite3
from datetime import datetime
import os

conn = sqlite3.connect("shop.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS items(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    file_path TEXT,
    price REAL
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    balance REAL DEFAULT 0
)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item_id INTEGER,
    quantity INTEGER,
    total_price REAL,
    timestamp DATETIME
)
""")
conn.commit()

def get_or_create_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, balance) VALUES (?, ?)", (user_id, 0))
        conn.commit()
        return (user_id, 0)
    return user

def update_balance(user_id, amount):
    cursor.execute("UPDATE users SET balance=balance + ? WHERE user_id=?", (amount, user_id))
    conn.commit()

def get_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    res = cursor.fetchone()
    return res[0] if res else 0

def add_item(name, file_path, price):
    cursor.execute("INSERT INTO items (name, file_path, price) VALUES (?, ?, ?)",
                   (name, file_path, price))
    conn.commit()

def get_item(item_id):
    cursor.execute("SELECT * FROM items WHERE id=?", (item_id,))
    return cursor.fetchone()

def get_all_items():
    cursor.execute("SELECT * FROM items")
    return cursor.fetchall()

def create_order(user_id, item_id, quantity, total_price):
    timestamp = datetime.now()
    cursor.execute("INSERT INTO orders (user_id, item_id, quantity, total_price, timestamp) VALUES (?, ?, ?, ?, ?)",
                   (user_id, item_id, quantity, total_price, timestamp))
    conn.commit()
