"""
Authentication and authorization utilities.
"""
from datetime import datetime, timedelta
from typing import Optional
import hashlib
import secrets
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader

from config import settings

# Security schemes
bearer_scheme = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    Uses SHA256 with salt (format: salt$hash)
    """
    try:
        if "$" not in hashed_password:
            return False
        salt, hash_value = hashed_password.split("$", 1)
        computed_hash = hashlib.sha256((salt + plain_password).encode()).hexdigest()
        return secrets.compare_digest(computed_hash, hash_value)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """
    Generate password hash using SHA256 with salt.
    Format: salt$hash
    """
    salt = secrets.token_hex(16)
    hash_value = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}${hash_value}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: JWT token to decode
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )



async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)
) -> dict:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: Bearer token credentials
        
    Returns:
        User data from token
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return {"user_id": user_id, "email": payload.get("email")}


async def verify_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> bool:
    """
    Dependency to verify API key for webhook authentication.
    
    Args:
        api_key: API key from header
        
    Returns:
        True if API key is valid
        
    Raises:
        HTTPException: If API key is invalid or missing
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is missing",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    return True


class RoleChecker:
    """Dependency class to check user roles."""
    
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    
    async def __call__(self, user: dict = Depends(get_current_user)) -> dict:
        """
        Check if user has required role.
        
        Args:
            user: Current user from token
            
        Returns:
            User data if authorized
            
        Raises:
            HTTPException: If user doesn't have required role
        """
        user_role = user.get("role", "user")
        
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return user


# Role-based dependencies
require_admin = RoleChecker(["admin"])
require_operator = RoleChecker(["admin", "operator"])
