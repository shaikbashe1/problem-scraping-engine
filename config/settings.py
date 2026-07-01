import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# App Configurations
DEFAULT_LOG_PATH = BASE_DIR / "logs" / "engine.log"
METADATA_DIR = BASE_DIR / "metadata"
PROMPTS_DIR = BASE_DIR / "prompts"

# Similarity configuration
SIMILARITY_THRESHOLD = 0.85

# Validation timeout (in seconds per language)
VALIDATION_TIMEOUT = 5.0
