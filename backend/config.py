import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError(
        "CRITICAL ERROR: The 'GEMINI_API_KEY' environment variable is missing. "
        "Please specify it in your .env file or environment variables before running the application."
    )
