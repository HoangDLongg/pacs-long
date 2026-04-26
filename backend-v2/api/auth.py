# api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.auth_utils import AuthUtils
from database.connection import get_db
from models.user import User
from models.refresh_token import RefreshToken

# ====================== Pydantic Schemas ======================
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


# ====================== Router ======================
router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """POST /api/auth/login - Đăng nhập"""
    
    user = db.query(User).filter(
        User.username == body.username,
        User.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tài khoản hoặc mật khẩu"
        )

    if not AuthUtils.verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tài khoản hoặc mật khẩu"
        )

    # Tạo tokens
    access_token = AuthUtils.create_access_token(user)
    refresh_token = AuthUtils.create_refresh_token(user.id, db)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role
        }
    }


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    """POST /api/auth/refresh - Làm mới Access Token"""
    
    user = AuthUtils.verify_refresh_token(body.refresh_token, db)

    # Tạo token mới (có rotation refresh token)
    new_access_token = AuthUtils.create_access_token(user)
    new_refresh_token = AuthUtils.create_refresh_token(user.id, db)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role
        }
    }


@router.post("/logout")
def logout(body: RefreshRequest, db: Session = Depends(get_db)):
    """POST /api/auth/logout - Đăng xuất và thu hồi refresh token"""
    
    try:
        # Xác thực refresh token trước khi revoke
        user = AuthUtils.verify_refresh_token(body.refresh_token, db)
        
        # Revoke refresh token (đánh dấu revoked = True)
        db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked == False
        ).update({"revoked": True})
        
        db.commit()
        
        return {"message": "Đăng xuất thành công"}
        
    except HTTPException:
        # Nếu refresh token không hợp lệ vẫn cho logout (an toàn hơn)
        return {"message": "Đăng xuất thành công"}


@router.get("/me")
def get_me(current_user: User = Depends(AuthUtils.get_current_user)):
    """GET /api/auth/me - Lấy thông tin user hiện tại"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active
    }