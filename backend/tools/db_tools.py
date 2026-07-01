from sqlalchemy import extract

from backend.database.db import SessionLocal
from backend.database.models import SlackLog

def get_monthly_aggregates(month: int, year: int) -> dict:
    db = SessionLocal()
    try:
        logs = db.query(SlackLog).filter(
            extract("month", SlackLog.log_date) == month,
            extract("year", SlackLog.log_date) == year,
        ).all()

        total = sum(log.amount for log in logs)

        by_category = {}
        by_merchant = {}

        for log in logs:
            cat = log.category or "Other"
            by_category[cat] = by_category.get(cat, 0) + log.amount

            if log.merchant:
                by_merchant[log.merchant] = by_merchant.get(log.merchant, 0) + log.amount

        top_merchant = max(by_merchant, key=by_merchant.get) if by_merchant else None

        return {
            "month": month,
            "year": year,
            "total_spent": total,
            "by_category": by_category,
            "top_merchant": top_merchant,
            "transaction_count": len(logs),
        }
    finally:
        db.close()