import truststore
truststore.inject_into_ssl()

import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
OPENSKY_CLIENT_ID = os.getenv("OPENSKY_CLIENT_ID")
OPENSKY_CLIENT_SECRET = os.getenv("OPENSKY_CLIENT_SECRET")

CORS_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
    ).split(",")
    if origin.strip()
]

ASK_RATE_LIMIT_PER_MINUTE = int(os.getenv("ASK_RATE_LIMIT_PER_MINUTE", "10"))
WEATHER_RATE_LIMIT_PER_MINUTE = int(os.getenv("WEATHER_RATE_LIMIT_PER_MINUTE", "20"))

LANGUAGE_NAMES = {"en": "English", "pt": "Brazilian Portuguese"}