# main.py
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from database.connection import (
    init_db,
    close_all_connections,
    get_connection,
    release_connection,
)
from api import auth, worklist, dicom, report, dicom_editor, admin, search, ask
from config import ORTHANC_URL


# ====================== Lifespan (thay on_event deprecated) ======================
@asynccontextmanager
async def lifespan(app):
    """Startup → yield → Shutdown"""
    print("[PACS++] Starting server...")
    try:
        init_db()
        print("[PACS++] Database initialized successfully!")
    except Exception as e:
        print(f"[PACS++] Database initialization failed: {e}")
    yield
    print("[PACS++] Shutting down server...")
    close_all_connections()
    print("[PACS++] All database connections closed.")


# ====================== Rate Limiter ======================
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# Tạo FastAPI app
app = FastAPI(
    title="PACS++ API",
    version="2.0",
    description="Backend cho hệ thống PACS với Auth + DICOM + RAG",
    lifespan=lifespan,
)

# Gắn rate limiter vào app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - Nên giới hạn origin ở production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React dev
        "http://127.0.0.1:3000",
        "http://localhost:5173",      # Vite default
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== Đăng ký Routers ======================
# Lưu ý: mỗi router đã có prefix riêng — KHÔNG thêm prefix ở đây
app.include_router(auth.router)          # prefix=/api/auth (trong auth.py)
app.include_router(worklist.router)      # prefix=/api/worklist
app.include_router(dicom.router)         # prefix=/api/dicom
app.include_router(report.router)        # prefix=/api/report
app.include_router(dicom_editor.router)  # prefix=/api/editor
app.include_router(admin.router)         # prefix=/api/admin
app.include_router(search.router)        # prefix=/api/search (UC12-14)
app.include_router(ask.router)           # prefix=/api/ask (UC15)


# ====================== Health Check ======================
def _check_database() -> dict:
    """Ping PostgreSQL bằng SELECT 1."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "down", "error": str(e)[:200]}
    finally:
        if conn is not None:
            release_connection(conn)


def _check_orthanc() -> dict:
    """Ping Orthanc REST API. Orthanc tùy chọn → 'degraded' thay vì 'down'."""
    try:
        import requests
        resp = requests.get(f"{ORTHANC_URL}/system", timeout=2)
        if resp.ok:
            return {"status": "ok"}
        return {"status": "degraded", "http": resp.status_code}
    except Exception as e:
        return {"status": "degraded", "error": str(e)[:200]}


@app.get("/health")
def health_check():
    """Health check: DB bắt buộc OK, Orthanc optional.

    Returns 200 nếu DB OK (kể cả Orthanc degraded).
    Returns 503 nếu DB down.
    """
    db = _check_database()
    orthanc = _check_orthanc()

    overall_ok = db["status"] == "ok"
    body = {
        "status": "ok" if overall_ok else "degraded",
        "service": "PACS++ API v2",
        "version": "2.0",
        "checks": {
            "database": db,
            "orthanc": orthanc,
        },
    }
    return JSONResponse(status_code=200 if overall_ok else 503, content=body)


# ====================== Editor Page ======================
@app.get("/editor")
def editor_page():
    """Trang DICOM Name Editor"""
    html_path = os.path.join(os.path.dirname(__file__), "templates", "editor.html")
    if os.path.exists(html_path):
        return FileResponse(html_path, media_type="text/html")
    return {"error": "editor.html not found"}


# ====================== Run Server ======================
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )