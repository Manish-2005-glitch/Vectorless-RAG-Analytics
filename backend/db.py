import asyncpg
import os

DATABASE_URL = os.getenv("DATABASE_URL")

pool = None

async def get_pool():
    global pool
    if pool is None:
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL environment variable is not set")
        
        pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=5,
            command_timeout = 10
            )
        
    return pool