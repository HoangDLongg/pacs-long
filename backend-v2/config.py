import os
from dotenv import load_dotenv

load_dotenv()

# Database
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "pacs_db")
DB_USER = os.getenv("DB_USER", "pacs_user")
DB_PASS = os.getenv("DB_PASS", "pacs_pass")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Orthanc
ORTHANC_URL = os.getenv("ORTHANC_URL", "http://localhost:8042")

# JWT
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET or len(JWT_SECRET) < 32:
    raise ValueError("JWT_SECRET phải được thiết lập trong .env với độ dài ít nhất 32 ký tự (khuyến nghị 64+)")

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# OLLAMA
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# App settings
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = APP_ENV == "development"
ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")]