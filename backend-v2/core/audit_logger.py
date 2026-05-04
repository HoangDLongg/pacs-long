"""
core/audit_logger.py — Audit Logging cho PACS++
Ghi lại ai làm gì, lúc nào, trên endpoint nào.
Lưu vào file logs/audit.log (JSON Lines format).
"""
import os
import json
import logging
from datetime import datetime
from fastapi import Request

# Tạo thư mục logs nếu chưa có
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Audit logger — ghi vào file riêng
audit_logger = logging.getLogger("pacs.audit")
audit_logger.setLevel(logging.INFO)
audit_logger.propagate = False  # Không ghi vào console

# File handler — JSON Lines format
handler = logging.FileHandler(
    os.path.join(LOG_DIR, "audit.log"),
    encoding="utf-8"
)
handler.setFormatter(logging.Formatter("%(message)s"))
audit_logger.addHandler(handler)


def log_action(
    request: Request,
    action: str,
    detail: str = "",
    user_id: int = None,
    username: str = None,
    role: str = None,
):
    """Ghi 1 dòng audit log (JSON).

    Args:
        request: FastAPI Request object
        action: Hành động (LOGIN, UPLOAD_DICOM, CREATE_REPORT, SEARCH, ASK, etc.)
        detail: Chi tiết bổ sung
        user_id: ID user thực hiện
        username: Username
        role: Role
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "user_id": user_id,
        "username": username,
        "role": role,
        "ip": request.client.host if request.client else "unknown",
        "method": request.method,
        "path": str(request.url.path),
        "detail": detail,
    }

    audit_logger.info(json.dumps(entry, ensure_ascii=False))


# Các action constants
class AuditAction:
    LOGIN = "LOGIN"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    UPLOAD_DICOM = "UPLOAD_DICOM"
    CREATE_REPORT = "CREATE_REPORT"
    UPDATE_REPORT = "UPDATE_REPORT"
    EXPORT_PDF = "EXPORT_PDF"
    SEARCH = "SEARCH"
    ASK_NL2SQL = "ASK_NL2SQL"
    ADMIN_VIEW_USERS = "ADMIN_VIEW_USERS"
    ADMIN_UPDATE_USER = "ADMIN_UPDATE_USER"
    RATE_LIMITED = "RATE_LIMITED"
