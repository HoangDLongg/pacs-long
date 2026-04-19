# main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from database.connection import (
    init_db,
    close_all_connections,
)
from api import auth, worklist, dicom, report, dicom_editor, admin

# Tạo FastAPI app
app = FastAPI(
    title="PACS++ API",
    version="2.0",
    description="Backend cho hệ thống PACS với Auth + DICOM"
)

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


# ====================== Health Check ======================
@app.get("/health")
def health_check():
    return {
        "status": "ok", 
        "service": "PACS++ API v2",
        "version": "2.0"
    }


# ====================== Editor Page ======================
@app.get("/editor")
def editor_page():
    """Trang DICOM Name Editor"""
    html_path = os.path.join(os.path.dirname(__file__), "templates", "editor.html")
    if os.path.exists(html_path):
        return FileResponse(html_path, media_type="text/html")
    return {"error": "editor.html not found"}


# ====================== Startup & Shutdown Events ======================
@app.on_event("startup")
async def on_startup():
    """Chạy khi server khởi động"""
    print("[PACS++] Starting server...")
    try:
        init_db()                    # Tạo bảng từ init_db.sql
        print("[PACS++] Database initialized successfully!")
    except Exception as e:
        print(f"[PACS++] Database initialization failed: {e}")


@app.on_event("shutdown")
async def on_shutdown():
    """Chạy khi server tắt"""
    print("[PACS++] Shutting down server...")
    close_all_connections()
    print("[PACS++] All database connections closed.")


# ====================== Run Server ======================
if __name__ == "__main__":
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )