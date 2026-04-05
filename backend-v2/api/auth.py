import os
import sys

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_utils import AuthUtils
from database.connection import DatabaseConnection
from psycopg2.extras import RealDictCursor

# Tạo router — nhóm các endpoint liên quan tới auth
router = APIRouter(prefix="/api/auth", tags=["Auth"])


# Model dữ liệu đầu vào — FastAPI tự validate
class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(body: LoginRequest):
    """POST /api/auth/login — Đăng nhập, trả JWT token"""
    conn = DatabaseConnection.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 1. Tìm user theo username
        cursor.execute("SELECT * FROM users WHERE username = %s", (body.username,))
        user = cursor.fetchone()

        # 2. Không tìm thấy
        if not user:
            raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")

        # 3. Sai password
        if not AuthUtils.verify_password(body.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Sai tài khoản hoặc mật khẩu")

        # 4. Tài khoản bị khoá
        if not user["is_active"]:
            raise HTTPException(status_code=403, detail="Tài khoản đã bị khoá")

        # 5. Tạo token
        token = AuthUtils.create_token(user["id"], user["username"], user["role"])

        return {
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "full_name": user["full_name"],
                "role": user["role"]
            }
        }
    finally:
        cursor.close()
        DatabaseConnection.release_connection(conn)


@router.get("/me")
def get_me(request: Request):
    """GET /api/auth/me — Lấy thông tin user đang đăng nhập"""
    current_user = AuthUtils.get_current_user(request)
    return current_user
