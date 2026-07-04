import sys
import os
from sqlalchemy import text

# Add backend directory to path if run directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from backend.database.db import engine
except ModuleNotFoundError:
    from database.db import engine

def migrate():
    with engine.connect() as conn:
        print("Starting migration...")
        
        # Add time column
        try:
            conn.execute(text("ALTER TABLE bank_transactions ADD COLUMN time TIME;"))
            conn.commit()
            print("Successfully added column 'time' to bank_transactions.")
        except Exception as e:
            print(f"Column 'time' might already exist or failed to add: {e}")
            
        # Add notes column
        try:
            conn.execute(text("ALTER TABLE bank_transactions ADD COLUMN notes TEXT;"))
            conn.commit()
            print("Successfully added column 'notes' to bank_transactions.")
        except Exception as e:
            print(f"Column 'notes' might already exist or failed to add: {e}")

if __name__ == "__main__":
    migrate()
