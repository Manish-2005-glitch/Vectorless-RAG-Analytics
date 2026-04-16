import os
import re
import sqlglot
from sqlglot import expressions as exp
from openai import OpenAI
from backend.db import get_pool
from backend.cache import get_cache, set_cache
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


def clean_sql_output(text):
    text = text.strip()

    text = text.replace("```sql", "").replace("```", "").strip()

    match = re.search(r"(SELECT[\s\S]+?;)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    match = re.search(r"(SELECT[\s\S]+)", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return text


def validate_sql(sql):
    try:
        parsed = sqlglot.parse_one(sql)

        for node in parsed.walk():
            if isinstance(node, (exp.Delete, exp.Update, exp.Insert)):
                return False

        return True

    except Exception as e:
        print("SQL Parse Error:", e)
        return False


async def generate_sql(question):
    prompt = f"""
You are a PostgreSQL expert.

Return ONLY a valid SQL SELECT query.
Do NOT include explanations.
Do NOT include any text before or after SQL.

Schema:
{SCHEMA}

{OPTIMIZATION_HINTS}

Question: {question}

SQL:
"""

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    raw_output = response.choices[0].message.content

    sql = clean_sql_output(raw_output)

    print("\n--- LLM RAW OUTPUT ---\n", raw_output)
    print("\n--- CLEAN SQL ---\n", sql)

    return sql

async def execute_sql(sql):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(sql)


async def explain_result(question, result):
    prompt = f"""
Question: {question}

Result (sample): {result[:5]}

Explain the result in 2-3 lines in simple terms.
"""

    response = client.chat.completions.create(
        model="openai/gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()


async def run_query(question):
    cache_key = f"q:{question}"

    cached = get_cache(cache_key)
    if cached:
        print("Cache hit")
        return cached

    for attempt in range(2):
        sql = await generate_sql(question)

        if not validate_sql(sql):
            print("Invalid SQL generated")
            continue

        try:
            result = await execute_sql(sql)

            explanation = await explain_result(question, result)

            response = {
                "sql": sql,
                "result": [dict(r) for r in result],
                "explanation": explanation
            }

            set_cache(cache_key, response)

            return response

        except Exception as e:
            print("Execution Error:", e)
            continue

    return {"error": "Failed after retries."}