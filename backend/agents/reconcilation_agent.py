import json
try:
    from backend.database.db import SessionLocal
    from backend.database.models import SlackLog, BankTransaction, UpiPattern, MonthlySummary
    from backend.agents.ingestion_agent import ingestion_pipeline
except ModuleNotFoundError:
    from database.db import SessionLocal
    from database.models import SlackLog, BankTransaction, UpiPattern, MonthlySummary
    from agents.ingestion_agent import ingestion_pipeline
from datetime import timedelta, datetime, time


def full_pipeline(raw_transactions: list[dict], file_name: str):
    """
    Runs ingestion → reconciliation → summary rebuild, all in one background task.
    """
    # Step 1: Ingestion
    ingestion_result = ingestion_pipeline(raw_transactions, file_name)
    print(f"Ingestion done: {ingestion_result}")

    # Step 2: Reconciliation (runs on ALL unreconciled transactions, not just this upload)
    reconciliation_result = run_reconciliation()
    print(f"Reconciliation done: {reconciliation_result}")

    # Step 3: Rebuild summary for the affected month(s)
    months_years = {(t["month"], t["year"]) for t in raw_transactions}
    db = SessionLocal()
    try:
        for month, year in months_years:
            rebuild_monthly_summary(db, month, year)
    finally:
        db.close()

    print("Full pipeline completed.")


def run_reconciliation():
    db = SessionLocal()
    matched_count = 0
    annotation_count = 0

    try:
        bank_logs = db.query(BankTransaction).filter(
            BankTransaction.reconcile_status == None,
        ).all()

        if not bank_logs:
            return {"message": "No transactions left to reconcile"}

        for bank_log in bank_logs:
            slack_logs = db.query(SlackLog).filter(
                SlackLog.log_date >= bank_log.date - timedelta(days=1),
                SlackLog.log_date <= bank_log.date + timedelta(days=1),
                SlackLog.matched_txn_id == None
            ).all()

            # 1. Filter candidates by amount tolerance (<= 0.1 variance)
            candidate_matches = [
                log for log in slack_logs 
                if abs(bank_log.amount - log.amount) <= 0.1
            ]

            if not candidate_matches:
                # No matches found -> Send to Dashboard
                bank_log.needs_annotation = True
                bank_log.reconcile_status = "needs_annotation"
                annotation_count += 1

            else:
                # 2. Tie-breaker: If >1 match, find the closest one in time
                if len(candidate_matches) > 1:
                    matched_slack_log = min(
                        candidate_matches, 
                        key=lambda log: abs(
                            (datetime.combine(bank_log.date, bank_log.time or time.min) - 
                             (log.created_at or datetime.combine(log.log_date, time.min))).total_seconds()
                        )
                    )
                    # flag that this was an auto-resolved ambiguous match
                    bank_log.notes = "auto-resolved: multiple candidates, closest time selected"
                else:
                    matched_slack_log = candidate_matches[0]

                # 3. Apply the match
                bank_log.needs_annotation = False
                bank_log.reconcile_status = "matched"
                bank_log.slack_log_id     = matched_slack_log.id
                bank_log.category         = matched_slack_log.category
                bank_log.subcategory      = matched_slack_log.subcategory
                bank_log.reason           = matched_slack_log.reason
                matched_slack_log.matched_txn_id = bank_log.id
                matched_count += 1

                # 4. Pattern Memory Update
                existing_pattern = db.query(UpiPattern).filter(
                    UpiPattern.upi_id == bank_log.upi_name
                ).first()
                
                if existing_pattern:
                    existing_pattern.occurrence_count += 1
                    existing_pattern.last_seen = bank_log.date
                else:
                    db.add(UpiPattern(
                        upi_id              = bank_log.upi_name,
                        learned_category    = matched_slack_log.category,
                        learned_subcategory = matched_slack_log.subcategory,
                        learned_name        = bank_log.upi_name,
                        occurrence_count    = 1,
                        user_confirmed      = False,
                        last_seen           = bank_log.date
                    ))
            db.commit()
        affected_months_years = {(bank_log.month, bank_log.year) for bank_log in bank_logs}
        for month, year in affected_months_years:
            rebuild_monthly_summary(db, month, year)
        
        return {
            "message":          "Reconciliation completed",
            "matched":          matched_count,
            "needs_annotation": annotation_count,
        }

    except Exception as e:
        db.rollback()
        return {"message": "Reconciliation failed", "error": str(e)}

    finally:
        db.close()


def rebuild_monthly_summary(db,month,year):
    
    txns = db.query(BankTransaction).filter(BankTransaction.month == month, BankTransaction.year == year).all()

    total_debits = sum(txn.amount for txn in txns if txn.type =='debit')
    total_credits = sum(txn.amount for txn in txns if txn.type =='credit')
    by_category = {}
    for t in txns:
        if t.type == "debit":
            cat = t.category or "Uncategorized"
            sub = t.subcategory or "General"
            key = f"{cat} ({sub})"
            by_category[key] = by_category.get(key, 0) + t.amount
    
    top_merchant = max(
        by_category, key=by_category.get
    ) if by_category else None

    matched_count = len([t for t in txns if t.reconcile_status == "matched"])
    debit_count   = len([t for t in txns if t.type == "debit"])
    match_rate    = round(matched_count / debit_count, 2) if debit_count else 0.0


    existing = db.query(MonthlySummary).filter(
        MonthlySummary.month == month,
        MonthlySummary.year == year
    ).first()

    if existing:
        existing.total_debits    = total_debits
        existing.total_credits   = total_credits
        existing.by_category     = json.dumps(by_category)
        existing.top_merchant    = top_merchant
        existing.bank_txn_count  = len(txns)
        existing.match_rate      = match_rate
    else:
        db.add(MonthlySummary(
            month=month, year=year,
            total_debits=total_debits,
            total_credits=total_credits,
            by_category=json.dumps(by_category),
            top_merchant=top_merchant,
            bank_txn_count=len(txns),
            match_rate=match_rate,
        ))
    db.commit()
    