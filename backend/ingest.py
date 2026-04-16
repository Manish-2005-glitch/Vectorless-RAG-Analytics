import httpx
import asyncio
from backend.db import get_pool
from datetime import datetime

BASE_URL = "https://fakestoreapi.com"

async def fetch(endpoint):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/{endpoint}")
        return response.json()

def parse_date(date_str):
    try:
        return datetime.fromisoformat(date_str.replace("Z", ""))
    except Exception:
        return None

async def ingest():
    pool = await get_pool()
    
    users = await fetch("users")
    products = await fetch("products")
    carts = await fetch("carts")
    
    async with pool.acquire() as conn:
        for u in users:
            await conn.execute("""
                INSERT INTO users (id, email, username)
                VALUES ($1, $2, $3)
                ON CONFLICT (id) DO NOTHING
            """, u["id"], u["email"], u["username"])

        for p in products:
            await conn.execute("""
                INSERT INTO products (id, title, price, category)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO NOTHING
            """, p["id"], p["title"], p["price"], p["category"])

        for cart in carts:
            order_date = parse_date(cart["date"])

            await conn.execute("""
                INSERT INTO orders (id, user_id, date)
                VALUES ($1, $2, $3)
                ON CONFLICT (id) DO NOTHING
            """,
                cart["id"],
                cart["userId"],
                order_date)

            for item in cart["products"]:
                await conn.execute("""
                    INSERT INTO order_items (order_id, product_id, quantity)
                    VALUES ($1, $2, $3)
                """, cart["id"], item["productId"], item["quantity"])
                
                
if __name__ == "__main__":
    asyncio.run(ingest())