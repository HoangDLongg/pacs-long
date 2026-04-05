import os
import sys
from datetime import datetime, timedelta

from jose import jwt, JWTError
import bcrypt
from fastapi import Request, HTTPException

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import JWT_SECRET, JWT_EXPIRE_HOURS


class AuthUtils:
    """Xử lý password hashing + JWT token"""

    @classmethod
    def hash_password(cls, password: str) -> str:
        """'admin123' → '$2b$12$xYz...'"""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @classmethod
    def verify_password(cls, plain: str, hashed: str) -> bool:
        """So sánh password người nhập vs hash trong DB"""
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

    @classmethod
    def create_token(cls, user_id: int, username: str, role: str) -> str:
        """Tạo JWT token — chứa user info, hết hạn sau 8 giờ"""
        payload = {
            "sub": user_id,
            "username": username,
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    @classmethod
    def decode_token(cls, token: str) -> dict:
        """Giải mã JWT → lấy thông tin user"""
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

    @classmethod
    def get_current_user(cls, request: Request) -> dict:
        """Lấy user từ header Authorization: Bearer <token>"""
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing token")

        token = auth_header.split(" ")[1]

        try:
            payload = cls.decode_token(token)
            return payload
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")