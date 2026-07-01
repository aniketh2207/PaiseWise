from fastapi import FastAPI
from database.db import init_db, get_db
from database.seed import seed_categories
from tools.llm_client import parse_slack_expense

app = FastAPI(title="PaiseWise")

@app.on_event("startup")
def on_startup():
    init_db()
    seed_categories()

@app.get("/health")
def health_check():
    return {"status":"ok"}
    
@app.post("/test_slack_parser")
def test_parser(message):
    result = parse_slack_expense(message)
    return {
        "result": result
    }