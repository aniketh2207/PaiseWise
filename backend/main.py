from fastapi import FastAPI,File, UploadFile, HTTPException, BackgroundTasks
from database.db import init_db, get_db
from database.seed import seed_categories
from tools.llm_client import parse_slack_expense
from tools.pdf_parser import extract_gpay_transactions,get_file_hash
from typing import Annotated, Optional
from database.models import *
from database.db import SessionLocal
from agents.reconcilation_agent import full_pipeline, run_reconciliation
from agents.ingestion_agent import ingestion_pipeline
from pydantic import BaseModel
from tools.llm_client import generate_summary
from fastapi.responses import StreamingResponse
import io
from agents.report_agent import generate_report, send_report
import io
import json
from agents.parsing_agent import parse_agent
from agents.query_agent import generate_sql, generate_answer
from agents.router_agent import classify_intent, generate_conversational_reply

from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title="PaiseWise")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()
    seed_categories()
    try:
        from backend.tools.token_loader import load_gmail_token
    except ModuleNotFoundError:
        from tools.token_loader import load_gmail_token
    load_gmail_token()

@app.get("/health")
def health_check():
    return {"status":"ok"}
    
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
        background_tasks.add_task(full_pipeline, raw_transactions, file.filename)
        return {
            "status": "success",
            "filename": file.filename,
            "total_transactions": len(raw_transactions),
            "data": raw_transactions
        } 
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")


@app.post("/api/reconcile")
def trigger_reconciliation():
    """
    Manually triggers the pure Python reconciliation pipeline.
    Uses POST because it modifies database state (updates statuses, saves patterns).
    """
    result = run_reconciliation()
    return result

@app.get("/api/get_annotation_queue")
def get_transactions():
    db = SessionLocal()
    transactions = db.query(BankTransaction).filter(BankTransaction.needs_annotation==True).all()
    return { "data": transactions,'length':len(transactions)}


class AnnotationUpdate(BaseModel):
    category: str
    subcategory: str
    reason: str
    remember_upi: bool = False

@app.patch("/api/transactions/{txn_id}/annotate")
def annotate_transaction(txn_id: int, payload: AnnotationUpdate):
    db = SessionLocal()
    try:
        txn = db.query(BankTransaction).filter(BankTransaction.id == txn_id).first()
        if not txn:
            raise HTTPException(status_code=404, detail="Transaction not found")

        txn.category         = payload.category
        txn.subcategory       = payload.subcategory
        txn.reason            = payload.reason
        txn.reconcile_status  = "user_annotated"
        txn.needs_annotation  = False

        if payload.remember_upi:
            existing = db.query(UpiPattern).filter(
                UpiPattern.upi_id == txn.upi_name
            ).first()
            if existing:
                existing.learned_category    = payload.category
                existing.learned_subcategory = payload.subcategory
                existing.user_confirmed      = True
            else:
                db.add(UpiPattern(
                    upi_id              = txn.upi_name,
                    learned_name        = txn.upi_name,
                    learned_category    = payload.category,
                    learned_subcategory = payload.subcategory,
                    occurrence_count    = 1,
                    user_confirmed      = True,
                    last_seen           = txn.date,
                ))

        db.commit()
        return {"message": "Annotation saved"}
    except Exception as e:
        db.rollback()
        print("Error", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@app.get("/api/dashboard/summary")
def get_dashboard_summary(month: int = None, year: int = None):
    db = SessionLocal()
    try:
        if not month or not year:
            latest = db.query(MonthlySummary).order_by(
                MonthlySummary.year.desc(),
                MonthlySummary.month.desc()
            ).first()
            if latest:
                month = latest.month
                year = latest.year
            else:
                latest_txn = db.query(BankTransaction).order_by(
                    BankTransaction.year.desc(),
                    BankTransaction.month.desc()
                ).first()
                if latest_txn:
                    month = latest_txn.month
                    year = latest_txn.year
                else:
                    from datetime import datetime
                    now = datetime.now()
                    month = now.month
                    year = now.year

        db_summary = db.query(MonthlySummary).filter(
            MonthlySummary.month == month,
            MonthlySummary.year == year
        ).first()
        if not db_summary:
            return {"exists": False, "month": month, "year": year}

        pending = db.query(BankTransaction).filter(
            BankTransaction.needs_annotation == True,
            BankTransaction.month == month,
            BankTransaction.year == year
        ).count()

        txns_details = db.query(BankTransaction).filter(
            BankTransaction.month == month,
            BankTransaction.year == year,
            BankTransaction.type == 'debit'
        ).all()
        
        txn_lines = []
        for t in txns_details:
            desc = t.reason or t.raw_description or "Unknown spend"
            txn_lines.append(f"- {desc}: ₹{t.amount:.0f} (Category: {t.category or 'Other'}, Subcategory: {t.subcategory or 'General'})")

        by_category_data = json.loads(db_summary.by_category or "{}")

        # Map to the exact structure expected by generate_summary in llm_client.py
        aggregates_payload = {
            "month": month,
            "year": year,
            "total_spent": db_summary.total_debits or 0.0,
            "transaction_count": db_summary.bank_txn_count or 0,
            "by_category": by_category_data,
            "top_merchant": db_summary.top_merchant or "N/A",
            "transaction_list": "\n".join(txn_lines)
        }

        llm_summary = generate_summary(aggregates_payload)

        return {
            "exists": True,
            "total_debits": db_summary.total_debits or 0.0,
            "total_credits": db_summary.total_credits or 0.0,
            "by_category": by_category_data,
            "top_merchant": db_summary.top_merchant,
            "match_rate": db_summary.match_rate or 0.0,
            "pending_annotations": pending,
            "llm_summary": llm_summary
        }

    finally:
        db.close()

@app.get("/api/reports/generate")
def api_generate_report(month: int, year: int):
    result = generate_report(month, year)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return {"status": "success", "insights": result["insights"]}


@app.get("/api/reports/download")
def api_download_report(month: int, year: int):
    result = generate_report(month, year)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return StreamingResponse(
        io.BytesIO(result["excel_bytes"]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=PaiseWise_{month}_{year}.xlsx"},
    )


class SendReportRequest(BaseModel):
    month: int
    year: int
    recipient_ids: Optional[list[int]] = None

@app.post("/api/reports/send")
def api_send_report(payload: SendReportRequest):
    result = send_report(payload.month, payload.year, payload.recipient_ids)
    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
    return result


class RecipientCreate(BaseModel):
    name: str
    email: str

@app.get("/api/recipients")
def get_recipients():
    db = SessionLocal()
    try:
        return db.query(ReportRecipient).filter(ReportRecipient.active == True).all()
    finally:
        db.close()

@app.post("/api/recipients")
def add_recipient(payload: RecipientCreate):
    db = SessionLocal()
    try:
        db.add(ReportRecipient(name=payload.name, email=payload.email))
        db.commit()
        return {"message": "Recipient added"}
    finally:
        db.close()

        
@app.delete("/api/recipients/{recipient_id}")
def remove_recipient(recipient_id: int):
    db = SessionLocal()
    try:
        recipient = db.query(ReportRecipient).filter(ReportRecipient.id == recipient_id).first()
        if not recipient:
            raise HTTPException(status_code=404, detail="Recipient not found")
        
        recipient.active = False
        db.commit()
        return {"message": f"Recipient {recipient_id} deactivated"}
    finally:
        db.close()


class HistoryMessage(BaseModel):
    role: str
    content: str


class ChatMessage(BaseModel):
    message: str
    history: Optional[list[HistoryMessage]] = None


@app.post("/api/chat")
def handle_chat_message(payload: ChatMessage):
    """
    Single entrypoint for both expense logging and spending questions.
    Uses LLM-based intent classification to route messages.
    """
    from datetime import datetime
    from sqlalchemy import text

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    history_data = payload.history or []
    intent = classify_intent(message, history_data)
    print(f"[Router] Message: '{message}' -> Intent: '{intent}'")

    if intent == "query":
        db = SessionLocal()
        try:
            sql = generate_sql(message, history_data)
            result = db.execute(text(sql)).fetchall()
            answer = generate_answer(message, result, history_data)
            return {"type": "answer", "reply": answer}
        except Exception:
            import traceback
            traceback.print_exc()
            return {"type": "error", "reply": "Sorry, I couldn't process that question. Try rephrasing it."}
        finally:
            db.close()
    elif intent == "log":
        try:
            result = parse_agent.invoke({
                "raw_message": message,
                "slack_message_id": f"app_{datetime.now().timestamp()}",
                "channel_id": "mobile_app",
                "log_date": datetime.now().date().isoformat(),
            })
            reply = result.get("reply_message", "Logged successfully.")
            return {"type": "log", "reply": reply}
        except Exception:
            import traceback
            traceback.print_exc()
            return {"type": "error", "reply": "Sorry, I couldn't log that expense. Try rephrasing it."}
    elif intent == "followup":
        try:
            result = parse_agent.invoke({
                "raw_message": message,
                "slack_message_id": f"app_{datetime.now().timestamp()}",
                "channel_id": "mobile_app",
                "log_date": datetime.now().date().isoformat(),
            })
            reply = result.get("reply_message", "Logged successfully.")
            return {"type": "log", "reply": reply}
        except Exception:
            import traceback
            traceback.print_exc()
            return {"type": "error", "reply": "Sorry, I couldn't process that. Try rephrasing it."}
    elif intent == "conversational":
        reply = generate_conversational_reply(message, history_data)
        return {"type": "answer", "reply": reply}
    else:
        return {"type": "answer", "reply": "I'm not sure what you mean. Try asking a spending question or logging an expense!"}


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)