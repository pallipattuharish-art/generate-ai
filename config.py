"""
Configuration settings for AI Study Assistant.
Loads environment variables from .env file securely.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the application
BASE_DIR = Path(__file__).resolve().parent

# Load environment variables from .env file if it exists
load_dotenv(BASE_DIR / ".env")


class Config:
    """Base application configuration."""

    # Security
    SECRET_KEY = os.environ.get("SECRET_KEY", "study-assistant-dev-secret-key-2025")

    # Instance & Database Path
    INSTANCE_PATH = BASE_DIR / "instance"
    DATABASE_PATH = INSTANCE_PATH / "study_assistant.db"

    # Uploads Path & Restrictions
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH_MB", 16)) * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}

    # AI Service Settings
    AI_PROVIDER = os.environ.get("AI_PROVIDER", "gemini").lower().strip()
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash").strip()

    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()

    # Request timeouts (seconds)
    AI_TIMEOUT_SECONDS = 45


class TestConfig(Config):
    """Configuration for automated test execution."""

    TESTING = True
    DATABASE_PATH = Config.INSTANCE_PATH / "test_study_assistant.db"
    AI_PROVIDER = "demo"
