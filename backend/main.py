from fastapi import FastAPI
from models import create_tables
from ingest import ingest
from query_engine import run_query

app = FastAPI()

@app.on_event("startup")
async def startup():
    await create_tables()
    
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/query")
async def query(q: dict):
    question = q.get("question")
    
    if not question:
        return {"error": "Question is required."}
    
    result = await run_query(question)
    
    return result

@app.post("/refresh-data")
async def refresh():
    await ingest()
    return {"status": "data refreshed"}