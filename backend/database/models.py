from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, Text, UniqueConstraint
from sqlalchemy.sql import func

try:
    from backend.database.db import Base
except ModuleNotFoundError:
    from database.db import Base


class SlackLog(Base):
    __tablename__ = "slack_logs"
    id                = Column(Integer, primary_key=True, autoincrement=True)
    slack_message_id  = Column(String, unique=True, nullable=False)
    raw_message       = Column(Text, nullable=False)
    amount            = Column(Float, nullable=False)
    category          = Column(String)
    subcategory       = Column(String)
    reason            = Column(String)
    merchant          = Column(String)
    log_date          = Column(Date, nullable=False)
    channel_id        = Column(String)
    parse_confidence  = Column(Float, default=1.0)
    matched_txn_id    = Column(Integer)           # FK to BankTransaction.id (added later)
    created_at        = Column(DateTime, server_default=func.now())

class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    id                = Column(Integer, primary_key=True, autoincrement=True)
    date              = Column(Date, nullable=False)
    amount            = Column(Float, nullable=False)
    type              = Column(String, nullable=False)        # 'debit' | 'credit'
    upi_id            = Column(String)
    upi_name          = Column(String)
    raw_description   = Column(Text, nullable=False)
    is_business_upi   = Column(Boolean, default=False)
    reconcile_status  = Column(String)                       # matched | auto_categorized | needs_annotation | user_annotated
    category          = Column(String)
    subcategory       = Column(String)
    reason            = Column(String)
    slack_log_id      = Column(Integer)
    needs_annotation  = Column(Boolean, default=False)
    month             = Column(Integer, nullable=False)
    year              = Column(Integer, nullable=False)
    created_at        = Column(DateTime, server_default=func.now())

class UpiPattern(Base):
    __tablename__ = "upi_patterns"
    id                  = Column(Integer, primary_key=True, autoincrement=True)
    upi_id              = Column(String, unique=True, nullable=False)
    learned_name        = Column(String)
    learned_category    = Column(String)
    learned_subcategory = Column(String)
    occurrence_count    = Column(Integer, default=1)
    user_confirmed      = Column(Boolean, default=False)
    last_seen           = Column(Date)

class Category(Base):
    __tablename__ = "categories"
    id           = Column(Integer, primary_key=True, autoincrement=True)
    name         = Column(String, unique=True, nullable=False)
    parent       = Column(String)
    budget_limit = Column(Float)
    color_hex    = Column(String)

class MonthlySummary(Base):
    __tablename__ = "monthly_summaries"
    __table_args__ = (UniqueConstraint("month", "year"),)
    id              = Column(Integer, primary_key=True, autoincrement=True)
    month           = Column(Integer, nullable=False)
    year            = Column(Integer, nullable=False)
    total_debits    = Column(Float, default=0)
    total_credits   = Column(Float, default=0)
    by_category     = Column(Text)        # JSON string
    top_merchant    = Column(String)
    llm_insights    = Column(Text)
    slack_log_count = Column(Integer)
    bank_txn_count  = Column(Integer)
    match_rate      = Column(Float)
    report_path     = Column(String)
    report_sent_at  = Column(DateTime)

class ReportRecipient(Base):
    __tablename__ = "report_recipients"
    id     = Column(Integer, primary_key=True, autoincrement=True)
    name   = Column(String, nullable=False)
    email  = Column(String, unique=True, nullable=False)
    active = Column(Boolean, default=True)

class UploadLog(Base):
    __tablename__ = "upload_log"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    filename        = Column(String, nullable=False)
    file_hash       = Column(String, unique=True, nullable=False)
    month           = Column(Integer)
    year            = Column(Integer)
    rows_extracted  = Column(Integer)
    reconciled_at   = Column(DateTime)
    uploaded_at     = Column(DateTime, server_default=func.now())