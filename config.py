import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:20128/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "dummy-key")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "allin-v0.0.1")

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env")
