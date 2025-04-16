# Authentication module for PhishGuard
import os
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from dotenv import load_dotenv

# Import database functions
from backend.database import get_user_by_email, create_user

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "phishguard_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# Pydantic models
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

class UserCreate(BaseModel):
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: int
    email: str
    created_at: datetime

# Authentication functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash"""
    return pwd_context.hash(password)

def authenticate_user(email: str, password: str) -> Optional[Dict]:
    """Authenticate a user by email and password"""
    user = get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """Get the current user from a JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        user_id = payload.get("user_id")
        
        if email is None or user_id is None:
            raise credentials_exception
        
        token_data = TokenData(email=email, user_id=user_id)
    except jwt.PyJWTError:
        raise credentials_exception
    
    user = get_user_by_email(token_data.email)
    if user is None:
        raise credentials_exception
    
    return user

# User management functions
def register_new_user(user_data: UserCreate) -> Dict:
    """Register a new user"""
    # Check if user already exists
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        return {
            "success": False,
            "error": "Email already registered"
        }
    
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create the user
    user_id = create_user(user_data.email, hashed_password)
    
    if not user_id:
        return {
            "success": False,
            "error": "Failed to create user"
        }
    
    return {
        "success": True,
        "user_id": user_id
    }

def login_user(user_data: UserLogin) -> Dict:
    """Login a user and return an access token"""
    user = authenticate_user(user_data.email, user_data.password)
    
    if not user:
        return {
            "success": False,
            "error": "Incorrect email or password"
        }
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "user_id": user["id"]},
        expires_delta=access_token_expires
    )
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user["id"],
        "email": user["email"]
    }