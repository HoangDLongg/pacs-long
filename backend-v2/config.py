import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST","localhost")
DB_PORT = int(os.getenv("DB_PORT","5432"))
DB_NAME = os.getenv("DB_NAME","pacs_db")
DB_USER = os.getenv("DB_USER","pacs_user")
DB_PASS = os.getenv("DB_PASS","pacs_password")

ORTHANC_URL = os.getenv("ORTHANC_URL","http://localhost:8042")

JWT_SECRET = os.getenv("JWT_SECRET","pacs-secret-key-2026")
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS","8"))

OLLAMA_URL = os.getenv("OLLAMA_URL","http://localhost:11434")    