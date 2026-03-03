"""Authentication helpers: password hashing and session management."""

import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Request, HTTPException, status
from app.config import settings

serializer = URLSafeTimedSerializer(settings.SECRET_KEY)

SESSION_COOKIE_NAME = "session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def create_session_token(user_id: str) -> str:
    return serializer.dumps({"user_id": user_id})


def decode_session_token(token: str) -> dict | None:
    try:
        data = serializer.loads(token, max_age=SESSION_MAX_AGE)
        return data
    except (BadSignature, SignatureExpired):
        return None


def get_session_user_id(request: Request) -> str | None:
    """Extract user_id from session cookie, or None."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    data = decode_session_token(token)
    if data and "user_id" in data:
        return data["user_id"]
    return None


async def require_admin(request: Request):
    """FastAPI dependency: ensures request has valid admin session."""
    user_id = get_session_user_id(request)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/admin/login"},
        )
    request.state.user_id = user_id
    return user_id
