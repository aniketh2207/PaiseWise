from fastapi import FastAPI,File, UploadFile, HTTPException, BackgroundTasks
from database.db import init_db, get_db
from database.seed import seed_categories
from tools.llm_client import parse_slack_expense
from tools.pdf_parser import extract_gpay_transactions,get_file_hash
from typing import Annotated
from database.models import UploadLog
from database.db import SessionLocal
from agents.ingestion_agent import ingestion_pipeline
import io


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

@app.post("/api/upload-statement")
async def upload_bank_statement(file: UploadFile = File(...),background_tasks: BackgroundTasks = BackgroundTasks()):
    """
    API Endpoint to receive a PDF file and return the extracted structured data.
    """
    # 1. Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    try:
        # 2. Read file into memory
        file_contents = await file.read()
        
        # 3. Extract the raw data
        raw_transactions = extract_gpay_transactions(file_contents)
        # here we will call the ingestion pipeline, and also save the transactions
        
        if not raw_transactions:
            return {"status": "warning", "message": "No transactions found in the PDF.", "data": []}
            
        # 4. Get file hash
        file_hash = get_file_hash(file_contents)
        print(file_hash)
        
        db = SessionLocal()
        try:
            existing = db.query(UploadLog).filter(UploadLog.file_hash == file_hash).first()
            if existing:
                return {
                    "status": "warning",
                    "message": "This file has already been uploaded.",
                    "data_existing_rows_extracted": existing.rows_extracted
                }
            
            new_file = UploadLog(
                filename = file.filename,
                file_hash = file_hash,
                month = raw_transactions[0]["month"],
                year = raw_transactions[0]["year"],
                rows_extracted = len(raw_transactions)
            )
            db.add(new_file)
            db.commit()
        finally:
            db.close()
        
            
        # 5. Return the payload
        background_tasks.add_task(ingestion_pipeline, raw_transactions, file.filename)
        return {
            "status": "success",
            "filename": file.filename,
            "total_transactions": len(raw_transactions),
            "data": raw_transactions
        } 
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")

