import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # Running as PyInstaller standalone executable
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-sat-tracker-2026")
    _raw_db_url = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'assessment_tracker.db'}")
    if _raw_db_url and _raw_db_url.startswith("postgres://"):
        _raw_db_url = _raw_db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads & Reports Directories
    # In frozen mode, uploaded logos are stored persistently in <ExeDir>/uploads/
    UPLOAD_FOLDER = BASE_DIR / "uploads" if getattr(sys, "frozen", False) else BASE_DIR / "app" / "static" / "uploads"
    REPORT_FOLDER = BASE_DIR / "reports"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # AI Engine Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "groq")  # groq or openai
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama-3.3-70b-versatile")
    
    # School default branding
    DEFAULT_SCHOOL_NAME = os.getenv("DEFAULT_SCHOOL_NAME", "Delhi Public Model School")
