from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

try:
    from backend.config import settings
except ModuleNotFoundError:
    from config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    try:
        from backend.database import models
    except ModuleNotFoundError:
        from database import models
    Base.metadata.create_all(bind=engine)