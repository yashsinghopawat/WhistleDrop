import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings

password_hasher = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hasher.verify(plain_password, hashed_password)
    except ValueError:
        # bcrypt refuses passwords longer than 72 bytes
        return False


def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> int | None:
    """Returns the user id stored in the token, or None if the token is bad/expired."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def generate_case_code() -> str:
    # 8 random bytes = 64 bits of randomness, so it can't be guessed
    return "WD-" + secrets.token_hex(8).upper()


def hash_case_code(case_code: str) -> str:
    # Only the hash is stored in the database. If the database leaks,
    # the real case codes are still unknown.
    return hashlib.sha256(case_code.strip().upper().encode()).hexdigest()
