from db import get_pool

SCHEMA_SQL = """
BEGIN;

CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY,
    email TEXT,
    username TEXT
);

CREATE TABLE IF NOT EXISTS products (
    id INT PRIMARY KEY,
    title TEXT,
    price FLOAT,
    category TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    id INT PRIMARY KEY,
    user_id INT,
    date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT
);

CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);

COMMIT;
"""

async def create_tables():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(SCHEMA_SQL)