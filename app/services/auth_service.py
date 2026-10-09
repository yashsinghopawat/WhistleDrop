import secrets

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import LoginRequest, RegisterRequest


def register_moderator(db: Session, data: RegisterRequest) -> User:
    # Without this check anybody could make themselves a moderator
    if not secrets.compare_digest(data.invite_code, settings.moderator_invite_code):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid invite code")

    if user_repository.get_by_username(db, data.username):
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
    if user_repository.get_by_email(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    hashed = hash_password(data.password)
    return user_repository.create_user(db, data.username, data.email, hashed)


def login(db: Session, data: LoginRequest) -> str:
    user = user_repository.get_by_username(db, data.username)

    # same error for "no such user" and "wrong password" so attackers can't find valid usernames
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return create_access_token(user.id)
