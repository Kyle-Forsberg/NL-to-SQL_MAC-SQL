# AI-Generated: Claude-Sonnet-4
# Human Modified: Kyle Forsberg

#just so we have some data to play with, a for fun fake dataset from Claude.

import sqlite3
import os
from datetime import datetime, timedelta
import random


def create_sample_database(db_path: str = "sample_ecommerce.db"):
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        city TEXT,
        state TEXT,
        country TEXT DEFAULT 'USA',
        registration_date DATE,
        is_active BOOLEAN DEFAULT 1
    )
    """)
    
    cursor.execute("""
    CREATE TABLE categories (
        category_id INTEGER PRIMARY KEY,
        category_name TEXT NOT NULL,
        description TEXT
    )
    """)
    
    cursor.execute("""
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category_id INTEGER,
        price DECIMAL(10,2) NOT NULL,
        stock_quantity INTEGER DEFAULT 0,
        description TEXT,
        is_active BOOLEAN DEFAULT 1,
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER NOT NULL,
        order_date DATE NOT NULL,
        total_amount DECIMAL(10,2) NOT NULL,
        status TEXT DEFAULT 'pending',
        shipping_address TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
    )
    """)
    
    
    cursor.execute("""
    CREATE TABLE order_items (
        item_id INTEGER PRIMARY KEY,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        unit_price DECIMAL(10,2) NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(order_id),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    """)
    
    categories_data = [
        (1, 'Electronics', 'Electronic devices and gadgets'),
        (2, 'Clothing', 'Apparel and fashion items'),
        (3, 'Books', 'Books and educational materials'),
        (4, 'Home & Garden', 'Home improvement and garden supplies'),
        (5, 'Sports', 'Sports equipment and accessories')
    ]
    cursor.executemany("INSERT INTO categories VALUES (?, ?, ?)", categories_data)
    
    
    products_data = [
        (1, 'Laptop Pro 15"', 1, 1299.99, 50, 'High-performance laptop', 1),
        (2, 'Wireless Headphones', 1, 199.99, 100, 'Noise-canceling headphones', 1),
        (3, 'Smartphone X', 1, 899.99, 75, 'Latest smartphone model', 1),
        (4, 'Designer Jeans', 2, 89.99, 200, 'Premium denim jeans', 1),
        (5, 'Cotton T-Shirt', 2, 24.99, 500, 'Comfortable cotton t-shirt', 1),
        (6, 'Python Programming Book', 3, 49.99, 30, 'Learn Python programming', 1),
        (7, 'Garden Tools Set', 4, 79.99, 25, 'Complete garden tools set', 1),
        (8, 'Running Shoes', 5, 129.99, 150, 'Professional running shoes', 1),
        (9, 'Yoga Mat', 5, 39.99, 80, 'Premium yoga mat', 1),
        (10, 'Coffee Maker', 4, 159.99, 40, 'Automatic coffee maker', 1)
    ]
    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", products_data)
    
    
    customers_data = [
        (1, 'John', 'Smith', 'john.smith@email.com', '555-0101', 'New York', 'NY', 'USA', '2023-01-15', 1),
        (2, 'Sarah', 'Johnson', 'sarah.j@email.com', '555-0102', 'Los Angeles', 'CA', 'USA', '2023-02-20', 1),
        (3, 'Mike', 'Brown', 'mike.brown@email.com', '555-0103', 'Chicago', 'IL', 'USA', '2023-03-10', 1),
        (4, 'Emily', 'Davis', 'emily.davis@email.com', '555-0104', 'Houston', 'TX', 'USA', '2023-04-05', 1),
        (5, 'David', 'Wilson', 'david.wilson@email.com', '555-0105', 'Phoenix', 'AZ', 'USA', '2023-05-12', 1),
        (6, 'Lisa', 'Anderson', 'lisa.anderson@email.com', '555-0106', 'Philadelphia', 'PA', 'USA', '2023-06-18', 0),
        (7, 'James', 'Taylor', 'james.taylor@email.com', '555-0107', 'San Antonio', 'TX', 'USA', '2023-07-22', 1),
        (8, 'Maria', 'Garcia', 'maria.garcia@email.com', '555-0108', 'San Diego', 'CA', 'USA', '2023-08-14', 1)
    ]
    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", customers_data)
    
    order_id = 1
    for customer_id in range(1, 9):
        num_orders = random.randint(1, 4)  #Each customer has 1-4 orders
        
        for _ in range(num_orders):
            order_date = datetime(2023, random.randint(6, 12), random.randint(1, 28))
            num_items = random.randint(1, 3)  #items per order
            
            order_total = 0
            order_items = []
            
            for _ in range(num_items):  #randomize order further
                product_id = random.randint(1, 10)
                quantity = random.randint(1, 3)
                cursor.execute("SELECT price FROM products WHERE product_id = ?", (product_id,))
                unit_price = cursor.fetchone()[0]
                order_items.append((order_id, product_id, quantity, unit_price))
                order_total += quantity * unit_price
            
            status = random.choice(['completed', 'completed', 'completed', 'pending', 'shipped'])
            cursor.execute("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)", 
                         (order_id, customer_id, order_date.date(), order_total, status, f"{customer_id} Main St"))
            
            for item in order_items:
                cursor.execute("INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)", 
                             item)
            
            order_id += 1
    
    conn.commit()
    conn.close()
    
    print(f"Sample database created: {db_path}")
    print("Tables: customers, categories, products, orders, order_items")
    return db_path


if __name__ == "__main__":
    create_sample_database()
