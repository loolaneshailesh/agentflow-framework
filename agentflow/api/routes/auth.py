# agentflow/api/routes/auth.py
"""Authentication and user management routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import uuid

router = APIRouter(prefix="/auth", tags=["authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = "your-secret-key-change-in-production-please"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: Optional[str]
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# ── Helpers ───────────────────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def _get_user_model():
    """Lazily import User ORM model to avoid circular imports."""
    from agentflow.core.database import Base
    from sqlalchemy import Column, String, DateTime, Boolean

    # Return existing mapper if already registered
    if "users" in Base.metadata.tables:
        for mapper in Base.registry.mappers:
            if mapper.class_.__tablename__ == "users":
                return mapper.class_

    class User(Base):
        __tablename__ = "users"
        id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
        username = Column(String, unique=True, nullable=False)
        email = Column(String, unique=True, nullable=False)
        hashed_password = Column(String, nullable=False)
        full_name = Column(String, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        is_active = Column(Boolean, default=True)

    return User


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Decode JWT and return the current user."""
    from agentflow.core.database import SessionLocal
    User = _get_user_model()

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    finally:
        db.close()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """Register a new user."""
    from agentflow.core.database import SessionLocal, engine
    User = _get_user_model()
    from agentflow.core.database import Base
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = db.query(User).filter(
            (User.email == user.email) | (User.username == user.username)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email or username already registered")

        new_user = User(
            id=str(uuid.uuid4()),
            username=user.username,
            email=user.email,
            hashed_password=get_password_hash(user.password),
            full_name=user.full_name,
            created_at=datetime.utcnow(),
            is_active=True,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    finally:
        db.close()


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and return JWT access token."""
    from agentflow.core.database import SessionLocal
    User = _get_user_model()

    db = SessionLocal()
    try:
        # Accept login by email OR username
        user = db.query(User).filter(
            (User.email == form_data.username) | (User.username == form_data.username)
        ).first()

        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email/username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is inactive")

        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        return {"access_token": access_token, "token_type": "bearer", "user": user}
    finally:
        db.close()


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user=Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    full_name: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """Update current user profile."""
    from agentflow.core.database import SessionLocal
    db = SessionLocal()
    try:
        if full_name is not None:
            current_user.full_name = full_name
            db.add(current_user)
            db.commit()
            db.refresh(current_user)
        return current_user
    finally:
        db.close()


@router.post("/logout")
async def logout():
    """Logout (client should discard the token)."""
    return {"message": "Successfully logged out"}
