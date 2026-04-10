import redis
import os
from dotenv import load_dotenv
import json

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

r = redis.from_url(REDIS_URL, decode_responses=True)

def get_cache(key):
    data = r.get(key)
    return json.loads(data) if data else None

def set_cache(key, value, ttl=300):
    r.setex(key, ttl, json.dumps(value))