import os
import sqlglot
from sqlglot import expressions as exp
import openai
from db import get_pool
from cache import get_cache, set_cache

openai.api_key = os.getenv("OPENAI_API_KEY")

SCHEMA = """
users(id, email, username)
products(id, title, price, category)
orders(id, user_id, date)
order_items(id, order_id, product_id, quantity)

"""

OPTIMIZATION_HINTS = """
- Use LIMIT 100
- Avoid SELECT *
- Use indexed columns
- Filter early
"""

def validate_sql(sql):
    try:
        parsed = sqlglot.parse_one(sql)
        
        if not isinstance(parsed, exp.Select):
            return False
        
        for node in parsed.walk():
            if isinstance(node, (exp.Delete, exp.Update, exp.Insert)):
                return False
        
        return True    
        
    except:
        return False
    
    
async def generate_sql(question):
    prompt = f"""
    You are a SQL expert.PermissionError
    
    Schema:
    {SCHEMA}
    
    {OPTIMIZATION_HINTS}
    
    Only SELECT queries.
    
    Question: {question}
    
    SQL:
    """
    
    response = openai.ChatCompletion.create(
        model = "gpt-4o-mini",
        messages = [{"role": "user", "content": prompt}],
        temperature = 0
    )
    
    sql = response.choices[0].message["content"]
    return sql.replace("```","").strip()

async def execute_sql(sql):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(sql)
    
