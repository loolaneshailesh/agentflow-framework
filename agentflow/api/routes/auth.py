# agentflow/api/routes/auth.py
"""Authentication and user management routes - Enterprise Edition."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
import uuid

router = APIRouter(prefix="/auth", tags=["authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

SECRET_KEY = "your-secret-key-change-in-production-please"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

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

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """Register a new user."""
    from agentflow.core.database import SessionLocal
    from sqlalchemy import Column, String, DateTime, Boolean
    from sqlalchemy.ext.declarative import declarative_base
    
    Base = declarative_base()
    
    class User(Base):
        __tablename__ = "users"
        id = Column(String, primary_key=True)
        username = Column(String, unique=True)
        email = Column(String, unique=True)
        hashed_password = Column(String)
        full_name = Column(String)
        created_at = Column(DateTime)
        is_active = Column(Boolean)
    
    db = SessionLocal()
    try:
        # Check if user exists
        existing = db.query(User).filter(
            (User.email == user.email) | (User.username == user.username)
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Email or username already registered"
            )
        
        # Hash password
        hashed_pw = bcrypt.hashpw(
            user.password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        # Create user
        new_user = User(
            id=str(uuid.uuid4()),
            username=user.username,
            email=user.email,
            hashed_password=hashed_pw,
            full_name=user.full_name,
            created_at=datetime.utcnow(),
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    finally:
        db.close()

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login and get access token."""
    from agentflow.core.database import SessionLocal
    from sqlalchemy import Column, String, DateTime, Boolean
    from sqlalchemy.ext.declarative import declarative_base
    
    Base = declarative_base()
    
    class User(Base):
        __tablename__ = "users"
        id = Column(String, primary_key=True)
        username = Column(String)
        email = Column(String)
        hashed_password = Column(String)
        full_name = Column(String)
        created_at = Column(DateTime)
        is_active = Column(Boolean)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.email == form_data.username
        ).first()
        
        if not user or not bcrypt.checkpw(
            form_data.password.encode('utf-8'),
            user.hashed_password.encode('utf-8')
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        access_token = create_access_token(
            data={"sub": user.email},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current authenticated user."""
    from agentflow.core.database import SessionLocal
    from sqlalchemy import Column, String, DateTime, Boolean
    from sqlalchemy.ext.declarative import declarative_base
    
    Base = declarative_base()
    
    class User(Base):
        __tablename__ = "users"
        id = Column(String, primary_key=True)
        username = Column(String)
        email = Column(String)
        hashed_password = Column(String)
        full_name = Column(String)
        created_at = Column(DateTime)
        is_active = Column(Boolean)
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    finally:
        db.close()

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user = Depends(get_current_user)):
    """Get current user profile."""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    full_name: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """Update current user profile."""
    from agentflow.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        if full_name:
            current_user.full_name = full_name
            db.commit()
            db.refresh(current_user)
        return current_user
    finally:
        db.close()
