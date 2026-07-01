from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

try:
    from backend.config import settings
except ModuleNotFoundError:
    from config import settings

connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
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

# Your plan to initialize the cloud database:
if __name__ == "__main__":
    print(f"Connecting to: {settings.DATABASE_URL.split('@')[-1]}") # Safely prints the host, hiding credentials
    print("Creating database tables...")
    init_db()
    print("Database initialized successfully!")