import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from database.connection import DatabaseConnection
from api import auth, worklist, dicom, report, dicom_editor

# Tạo app
app = FastAPI(title="PACS++ API", version="2.0")

# CORS — cho phép frontend (port 5173) gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký tất cả routers
app.include_router(auth.router)
app.include_router(worklist.router)
app.include_router(dicom.router)
app.include_router(report.router)
app.include_router(dicom_editor.router)


@app.get("/health")
def health_check():
    """GET /health — Kiểm tra server sống"""
    return {"status": "ok", "service": "PACS++ API v2"}


@app.get("/editor")
def editor_page():
    """Trang DICOM Name Editor"""
    html_path = os.path.join(os.path.dirname(__file__), "templates", "editor.html")
    return FileResponse(html_path, media_type="text/html")


@app.on_event("startup")
def on_startup():
    """Chạy khi server khởi động — tạo bảng DB"""
    print("[PACS++] Starting server...")
    DatabaseConnection.init_db()
    print("[PACS++] Server ready!")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
