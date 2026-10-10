from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import UserCreate, UserLogin
from app.security import create_access_token, get_password_hash, verify_password

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
users_router = APIRouter(prefix="/api/users", tags=["Users"])
settings = get_settings()


@router.post("/register", status_code=201)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    username = payload.username.strip()
    email = payload.email.lower().strip()

    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(payload.password),
    )

    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username or email already exists") from exc

    return {
        "message": "Registration successful",
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }


@router.post("/login")
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter((User.username == payload.identifier) | (User.email == payload.identifier.lower())).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    expires_minutes = settings["ACCESS_TOKEN_EXPIRE_MINUTES"]
    access_token = create_access_token(str(user.id), expires_delta=timedelta(minutes=expires_minutes))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expires_minutes * 60,
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "email": current_user.email}


@users_router.get("/me")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "username": current_user.username, "email": current_user.email}


@router.post("/logout")
def logout_user():
    return {"message": "Logout successful. Please clear the client-side authentication state."}
