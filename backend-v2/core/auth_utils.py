# core/auth_utils.py
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError, ExpiredSignatureError
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Import theo model bạn vừa tạo
from models.user import User
from models.refresh_token import RefreshToken   # ← sẽ kiểm tra sau
from database.connection import get_db          # ← quan trọng
from config import (
    JWT_SECRET,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


class AuthUtils:

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    @staticmethod
    def create_access_token(user: User) -> str:
        """Tạo Access Token"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "exp": expire,
            "type": "access",
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: int, db: Session) -> str:
        """Tạo Refresh Token + lưu vào DB"""
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        refresh_token = jwt.encode(
            {"sub": str(user_id), "exp": expire, "type": "refresh"},
            JWT_SECRET,
            algorithm=JWT_ALGORITHM
        )

        token_hash = bcrypt.hashpw(refresh_token.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Xóa refresh token cũ của user
        db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()

        new_rt = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expire,
            revoked=False
        )

        db.add(new_rt)
        db.commit()

        return refresh_token

    @staticmethod
    def verify_refresh_token(refresh_token: str, db: Session) -> User:
        """Xác thực refresh token và trả về User object"""
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "refresh":
                raise JWTError("Invalid token type")

            user_id = int(payload["sub"])

            rt = db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc)
            ).first()

            if not rt or not bcrypt.checkpw(refresh_token.encode("utf-8"), rt.token_hash.encode("utf-8")):
                raise JWTError("Refresh token không hợp lệ hoặc đã bị thu hồi")

            user = db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).first()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Tài khoản không tồn tại hoặc đã bị khóa"
                )

            return user

        except (JWTError, ExpiredSignatureError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token không hợp lệ hoặc đã hết hạn"
            )

    @staticmethod
    def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
    ) -> User:
        """Lấy user từ Access Token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "access":
                raise JWTError("Invalid token type")

            user_id = int(payload["sub"])

            user = db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).first()

            if user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User không tồn tại hoặc bị vô hiệu hóa"
                )
            return user

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token không hợp lệ hoặc đã hết hạn",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    def get_current_user_optional(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
    ):
        """Như get_current_user nhưng trả None thay vì raise 401
        Dùng cho WADO endpoint — fallback khi không có Bearer header
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "access":
                return None
            user_id = int(payload["sub"])
            user = db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).first()
            return user
        except Exception:
            return None

    @staticmethod
    def validate_token_string(token: str, db: Session = None) -> User:
        """Validate raw token string (không qua Depends) — dùng cho query param token
        Dùng khi Cornerstone.js gửi token qua ?token= URL param
        """
        from database.connection import SessionLocal
        own_db = db is None
        db = db or SessionLocal()
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "access":
                raise HTTPException(status_code=401, detail="Token không hợp lệ")
            user_id = int(payload["sub"])
            user = db.query(User).filter(
                User.id == user_id,
                User.is_active == True
            ).first()
            if not user:
                raise HTTPException(status_code=401, detail="User không tồn tại")
            return user
        except JWTError:
            raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc hết hạn")
        finally:
            if own_db:
                db.close()