import logging
import os
import time

from fastapi import APIRouter, Depends, Header, HTTPException
from jose import JWTError, jwt
from pydantic import BaseModel

from app.infrastructure.storage.local.auth_store import (
    count_users,
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    list_users,
    set_user_department,
    update_user,
    verify_password,
)

logger = logging.getLogger(__name__)

_JWT_SECRET = os.environ["JWT_SECRET_KEY"]
_JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
_JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "1440"))

router = APIRouter(prefix="/auth", tags=["auth"])


def bootstrap_admin() -> None:
    # First run only: with no users yet there's no way to log in and create one, so
    # seed a single admin account from .env. Logged once so AanSensei knows to change it.
    if count_users() > 0:
        return
    email = os.environ.get("ADMIN_EMAIL", "admin@aanjsc.vn")
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not password:
        logger.warning("[auth] No users exist and ADMIN_PASSWORD is not set — set it in .env and restart.")
        return
    create_user(email, password, role="admin")
    logger.warning(f"[auth] Bootstrapped admin account: {email} — change the password after first login.")


def _create_access_token(user: dict) -> str:
    payload = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
        "exp": int(time.time()) + _JWT_EXPIRE_MINUTES * 60,
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)


async def get_current_user(authorization: str = Header(default="")) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization[len("Bearer "):]
    try:
        payload = jwt.decode(token, _JWT_SECRET, algorithms=[_JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = get_user_by_id(payload.get("sub", ""))
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")
    return user


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def get_collections(_user: dict = Depends(get_current_user)) -> list[str]:
    return []  # any authenticated user can see all collections — no per-user scoping yet


class LoginBody(BaseModel):
    email: str
    password: str


class CreateUserBody(BaseModel):
    email: str
    password: str
    role: str = "user"
    department: str | None = None


class UpdateMeBody(BaseModel):
    current_password: str
    new_email: str | None = None
    new_password: str | None = None


class UpdateDepartmentBody(BaseModel):
    department: str | None = None


@router.post("/login")
def login(body: LoginBody):
    user = get_user_by_email(body.email)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Sai email hoặc mật khẩu")
    public_user = {"id": user["id"], "email": user["email"], "role": user["role"], "created_at": user["created_at"], "department": user.get("department")}
    return {"access_token": _create_access_token(user), "token_type": "bearer", "user": public_user}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return user


@router.patch("/me")
def update_me(body: UpdateMeBody, user: dict = Depends(get_current_user)):
    full_user = get_user_by_email(user["email"])
    if not full_user or not verify_password(body.current_password, full_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Mật khẩu hiện tại không đúng")
    if body.new_email and get_user_by_email(body.new_email) and body.new_email.lower().strip() != user["email"]:
        raise HTTPException(status_code=409, detail="Email đã tồn tại")
    if body.new_password and len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 8 ký tự")
    return update_user(user["id"], email=body.new_email, password=body.new_password)


@router.get("/users")
def get_users(_admin: dict = Depends(require_admin)):
    return list_users()


@router.post("/users")
def add_user(body: CreateUserBody, _admin: dict = Depends(require_admin)):
    if get_user_by_email(body.email):
        raise HTTPException(status_code=409, detail="Email đã tồn tại")
    if body.role not in ("admin", "user"):
        raise HTTPException(status_code=400, detail="role phải là 'admin' hoặc 'user'")
    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 8 ký tự")
    return create_user(body.email, body.password, body.role, body.department)


@router.patch("/users/{user_id}/department")
def update_user_department(user_id: str, body: UpdateDepartmentBody, _admin: dict = Depends(require_admin)):
    updated = set_user_department(user_id, body.department)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated


@router.delete("/users/{user_id}")
def remove_user(user_id: str, admin: dict = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Không thể tự xóa tài khoản đang đăng nhập")
    if delete_user(user_id) == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"ok": True}
