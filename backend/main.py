from fastapi import FastAPI
from backend.models import create_tables
from backend.ingest import ingest
from backend.query_engine import run_query
from pydantic import BaseModel

app = FastAPI()

@app.on_event("startup")
async def startup():
    await create_tables()
    
@app.get("/health")
async def health():
    return {"status": "ok"}

class QueryRequest(BaseModel):
    question: str

@app.post("/query")
async def query(req: QueryRequest):
    return await run_query(req.question)

@app.post("/refresh-data")
async def refresh():
    await ingest()
    return {"status": "data refreshed"}