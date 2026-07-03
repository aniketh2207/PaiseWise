from database.db import SessionLocal
from database.models import BankTransaction
from tools.upi_classifier import classify_upi

def ingestion_pipeline(transactions: list[dict], file_name: str):
    saved, skipped = 0, 0
    
    # 1. Open the session ONCE for the entire pipeline
    db = SessionLocal()
    
    try:
        for txn in transactions:
            if txn.get("upi_transaction_id"):
                if is_already_ingested(txn["upi_transaction_id"], db):
                    skipped += 1
                    continue
                
                # 2. Pass the open db session to the classifier
                is_learned, category, subcategory = classify_upi(txn['upi_name'], db)
                
                # 3. Pass the open db session to the saver
                save_transaction(is_learned, category, subcategory, txn, db)
                saved += 1
                
        # Commit all saved transactions at once for massive speed gains
        db.commit()
        print("All the transactions are saved in the database")
        return {'saved': saved, 'skipped': skipped}
        
    except Exception as e:
        db.rollback()
        print(f"Pipeline failed: {e}")
        
    finally:
        # Close the connection when the whole loop is done
        db.close()


def is_already_ingested(upi_transaction_id: str, db) -> bool:
    # Ensure you are checking the actual transaction ID column, not the upi handle
    exists = db.query(BankTransaction).filter(BankTransaction.upi_id == upi_transaction_id).first()
    return exists is not None


def save_transaction(is_business: bool, category: str, subcategory: str, txn: dict, db):
    new_txn = BankTransaction(
        date=txn['date'],
        amount=txn['amount'],
        type=txn['type'],
        upi_id=txn.get('upi_transaction_id'), 
        upi_name=txn['upi_name'],
        raw_description=txn['raw_description'],
        month=txn['month'],
        year=txn['year'],
        
        # Handle the keys that aren't in the PDF parser by defaulting them
        is_business_upi=is_business,
        category=category,
        subcategory=subcategory,
        reconcile_status=None,       # Will be updated in Phase 3
        reason=None,                 # PDF transactions don't have reasons yet
        slack_log_id=None,           # Not linked to a slack log yet
        needs_annotation=not is_business # If it's not a known business, it needs review
    )
    db.add(new_txn)