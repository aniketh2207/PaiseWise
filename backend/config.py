import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Resolve the root directory of the project (one level up from backend/)
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./finance.db"
    #GEMINI_API_KEY: str
    SLACK_BOT_TOKEN: str
    SLACK_APP_TOKEN: str
    UPLOADS_DIR: str = "./uploads"
    REPORTS_DIR: str = "./reports"
    GEMINI_API_KEY: str
    GMAIL_TOKEN_PATH: str = str(BASE_DIR / "token.json")
    GMAIL_CREDENTIALS_PATH: str = str(BASE_DIR / "credentials.json")
    class Config:
        env_file = str(BASE_DIR / ".env")
        
settings = Settings()

# Force relative SQLite URLs to resolve to the backend folder absolutely
if "sqlite:///" in settings.DATABASE_URL:
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    if not os.path.isabs(db_path) and not db_path.startswith(":memory:"):
        if db_path.startswith("./"):
            db_path = db_path[2:]
        # Normalize the absolute path for Windows compatibility (replace backslashes with forward slashes)
        abs_db_path = os.path.normpath(os.path.join(BASE_DIR, "backend", db_path)).replace("\\", "/")
        settings.DATABASE_URL = f"sqlite:///{abs_db_path}"