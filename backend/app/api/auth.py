"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from app.auth import (
    create_access_token,
    verify_password,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter()


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserCreate(BaseModel):
    """User creation model."""
    email: EmailStr
    password: str
    role: str = "user"


# Temporary in-memory user store (replace with database in production)
# Pre-computed SHA256 hashes
# Format: salt$hash where hash = sha256(salt + password)
USERS_DB = {
    "admin@example.com": {
        "email": "admin@example.com",
        "hashed_password": "f11ab012a6adfae2ebef64d83f772b14$d45e8362c4c33e1b14ce4a68a8dab7c950fa99a77da9f43af4a8851f7ac09194",  # admin123
        "role": "admin"
    },
    "codenahiphatega@gmail.com": {
        "email": "codenahiphatega@gmail.com",
        "hashed_password": "2df6b563023bb54a85f0a7986ccc0f98$a81a5f35cd9adac5ebdb7c53815e2b8ed6b3cae9bbf81f7f21d0a61473e0017d",  # Gautam@2
        "role": "admin"
    }
}


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    
    Args:
        request: Login credentials
        
    Returns:
        JWT access token
        
    Raises:
        HTTPException: If credentials are invalid
    """
    user = USERS_DB.get(request.email)
    
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": request.email, "email": request.email, "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return LoginResponse(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: UserCreate):
    """
    Register a new user (for development/testing).
    
    Args:
        request: User creation data
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user already exists
    """
    if request.email in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    USERS_DB[request.email] = {
        "email": request.email,
        "hashed_password": get_password_hash(request.password),
        "role": request.role
    }
    
    return {"message": "User created successfully", "email": request.email}
