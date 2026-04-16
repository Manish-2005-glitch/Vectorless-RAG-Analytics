import redis
import os
from dotenv import load_dotenv
import json

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

print("Loaded REDIS_URL:", REDIS_URL)

try:
    if REDIS_URL:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        print("PING:", r.ping())
    else:
        print("No REDIS_URL found")
        r = None
except Exception as e:
    print("Redis Error:", e)
    r = None

def get_cache(key):
    data = r.get(key)
    return json.loads(data) if data else None

def set_cache(key, value, ttl=300):
    r.setex(key, ttl, json.dumps(value))