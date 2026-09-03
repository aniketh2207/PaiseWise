from datetime import datetime

try:
    from backend.database.db import SessionLocal
    from backend.database.models import MonthlySummary, ReportRecipient, BankTransaction
    from backend.tools.excel_builder import build_excel_report
    from backend.tools.email_sender import send_report_email
    from backend.tools.llm_client import generate_summary, generate_parent_report_summary
except ModuleNotFoundError:
    from database.db import SessionLocal
    from database.models import MonthlySummary, ReportRecipient, BankTransaction
    from tools.excel_builder import build_excel_report
    from tools.email_sender import send_report_email
    from tools.llm_client import generate_summary, generate_parent_report_summary

import os
from sqlalchemy.orm import Session

REPORTS_DIR = "./saved_reports"
os.makedirs(REPORTS_DIR, exist_ok=True) # Ensure the folder exists

def generate_report(month: int, year: int, db: Session = None, force_refresh: bool = False) -> dict:
    """
    Builds the Excel report, stores the LLM insights on MonthlySummary,
    and caches the file on disk.
    """
    local_db = False
    if db is None:
        db = SessionLocal()
        local_db = True
        
    try:
        summary = db.query(MonthlySummary).filter(
            MonthlySummary.month == month, MonthlySummary.year == year
        ).first()
        if not summary:
            return {"error": "No data found for this month. Upload and reconcile first."}
            
        if force_refresh:
            summary.llm_insights = None
            if summary.report_path and os.path.exists(summary.report_path):
                try:
                    os.remove(summary.report_path)
                except Exception:
                    pass
            summary.report_path = None
            db.commit()

        # 1. Generate LLM insights if not already present
        if not summary.llm_insights:
            import json
            # Query top 15 largest debit transactions for the month to help LLM analyze the report
            txns_details = db.query(BankTransaction).filter(
                BankTransaction.month == month,
                BankTransaction.year == year,
                BankTransaction.type == 'debit'
            ).order_by(BankTransaction.amount.desc()).limit(15).all()
            
            txn_lines = []
            for t in txns_details:
                desc = t.reason or t.raw_description or "Unknown spend"
                txn_lines.append(f"- {t.date.strftime('%Y-%m-%d')} {desc}: ₹{t.amount:.2f} (Category: {t.category or 'Other'})")
            
            aggregates = {
                "month": month,
                "year": year,
                "total_spent": summary.total_debits or 0.0,
                "total_credits": summary.total_credits or 0.0,
                "by_category": json.loads(summary.by_category or "{}"),
                "top_merchant": summary.top_merchant or "N/A",
                "transaction_count": summary.bank_txn_count or 0,
                "transaction_list": "\n".join(txn_lines) if txn_lines else "No transactions logged."
            }
            summary.llm_insights = generate_parent_report_summary(aggregates)
            db.commit()

        # 2. Check if the Excel report already exists on disk
        excel_bytes = None
        if summary.report_path and os.path.exists(summary.report_path):
            with open(summary.report_path, "rb") as f:
                excel_bytes = f.read()
        else:
            # Generate the report bytes
            excel_bytes = build_excel_report(month, year)
            
            # Save to disk
            file_name = f"PaiseWise_{year}_{month:02d}.xlsx"
            file_path = os.path.join(REPORTS_DIR, file_name)
            with open(file_path, "wb") as f:
                f.write(excel_bytes)
                
            # Update database
            summary.report_path = file_path
            db.commit()

        return {
            "status": "success",
            "insights": summary.llm_insights,
            "excel_bytes": excel_bytes,
        }
    finally:
        if local_db:
            db.close()


def send_report(month: int, year: int, recipient_ids: list[int] = None) -> dict:
    """
    Generates (or reuses) the report and emails it to recipients.
    """
    db = SessionLocal()
    try:
        result = generate_report(month=month, year=year, db=db)
        if result.get("status") != "success":
            return result

        query = db.query(ReportRecipient).filter(ReportRecipient.active == True)
        if recipient_ids:
            query = query.filter(ReportRecipient.id.in_(recipient_ids))
        recipients = query.all()

        if not recipients:
            return {"error": "No active recipients found."}

        month_name = datetime(year, month, 1).strftime("%B %Y")
        send_report_email(
            recipient_emails=[r.email for r in recipients],
            subject=f"PaiseWise — {month_name} Expense Report",
            body_text=result["insights"],
            excel_bytes=result["excel_bytes"],
            filename=f"PaiseWise_{month_name.replace(' ', '_')}.xlsx",
        )

        summary = db.query(MonthlySummary).filter(
            MonthlySummary.month == month, MonthlySummary.year == year
        ).first()
        summary.report_sent_at = datetime.now()
        db.commit()

        return {"status": "sent", "recipients": [r.email for r in recipients]}
    finally:
        db.close()