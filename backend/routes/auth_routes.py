"""Authentication routes: register, login, and current user profile."""

from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from limiter_config import limiter
from starlette.concurrency import run_in_threadpool

from database import get_db
from models.schemas import Token, UserCreate, UserLogin, UserOut
from utils.security import create_access_token, get_current_user_id, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _users():
    return get_db()["users"]


@router.post("/register", response_model=Token)
@limiter.limit("12/minute")
async def register_user(request: Request, payload: UserCreate):
    coll = _users()
    email = payload.email.lower().strip()

    existing = await run_in_threadpool(lambda: coll.find_one({"email": email}))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    now = datetime.now(timezone.utc)
    doc = {
        "email": email,
        "password": hash_password(payload.password),
        "full_name": payload.full_name,
        "created_at": now,
    }
    res = await run_in_threadpool(lambda: coll.insert_one(doc))
    token = create_access_token(str(res.inserted_id))
    return Token(access_token=token)


@router.post("/login", response_model=Token)
@limiter.limit("30/minute")
async def login_user(request: Request, payload: UserLogin):
    coll = _users()
    email = payload.email.lower().strip()
    user = await run_in_threadpool(lambda: coll.find_one({"email": email}))
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(str(user["_id"]))
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(user_id: str = Depends(get_current_user_id)):
    coll = _users()
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    user = await run_in_threadpool(lambda: coll.find_one({"_id": oid}))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserOut(
        id=str(user["_id"]),
        email=user["email"],
        full_name=user.get("full_name"),
        created_at=user.get("created_at"),
    )
