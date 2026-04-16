import os
import sqlglot
from sqlglot import expressions as exp
from openai import OpenAI
from db import get_pool
from cache import get_cache, set_cache
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

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
    
    response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
    
    sql = response.choices[0].message["content"]
    return sql.replace("```","").strip()

async def execute_sql(sql):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(sql)
    
async def explain_result(question, result):
    prompt = f"""
    Question: {question}
    Result: {result[:5]}
    
    Explain Briefly.
    """
    response = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
    
    return response.choices[0].message["content"]


async def run_query(question):
    cache_key = f"q:{question}"
    
    cached = await get_cache(cache_key)
    
    if cached:
        return cached
    
    for _ in range(2):
        sql = await generate_sql(question)
        
        if not validate_sql(sql):
            return {"error": "Generated SQL is not valid."}
        
        try:
            result = await execute_sql(sql)
            explanation = await explain_result(question, result)
            
            response = {
                "sql": sql,
                "result" : [dict(r) for r in result],
                "explanation": explanation
            }
            
            await set_cache(cache_key, response)
            return response
        
        except:
            continue
    
    return {"error": "Error executing SQL."}
