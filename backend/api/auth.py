"""Authentication and authorization utilities for the API."""
from datetime import datetime, timedelta
from typing import Optional, List
from enum import Enum

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Move to environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Security schemes
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    """User roles for authorization."""
    ADMIN = "admin"
    MANAGER = "manager"
    SALES = "sales"
    TECHNICAL = "technical"
    VIEWER = "viewer"


class User(BaseModel):
    """User model."""
    username: str
    email: str
    full_name: Optional[str] = None
    roles: List[UserRole] = Field(default_factory=list)
    disabled: bool = False


class UserInDB(User):
    """User model with hashed password."""
    hashed_password: str


class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: User


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    exp: Optional[datetime] = None


class LoginRequest(BaseModel):
    """Login request model."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class RegisterRequest(BaseModel):
    """Registration request model."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="Email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: Optional[str] = None
    roles: List[UserRole] = Field(default=[UserRole.VIEWER])


# Mock user database (replace with real database in production)
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@hakifmcg.com",
        "full_name": "Admin User",
        "hashed_password": pwd_context.hash("admin123"),
        "roles": [UserRole.ADMIN, UserRole.MANAGER],
        "disabled": False,
    },
    "sales_user": {
        "username": "sales_user",
        "email": "sales@hakifmcg.com",
        "full_name": "Sales User",
        "hashed_password": pwd_context.hash("sales123"),
        "roles": [UserRole.SALES],
        "disabled": False,
    },
    "tech_user": {
        "username": "tech_user",
        "email": "tech@hakifmcg.com",
        "full_name": "Technical User",
        "hashed_password": pwd_context.hash("tech123"),
        "roles": [UserRole.TECHNICAL],
        "disabled": False,
    },
    "viewer": {
        "username": "viewer",
        "email": "viewer@hakifmcg.com",
        "full_name": "Viewer User",
        "hashed_password": pwd_context.hash("viewer123"),
        "roles": [UserRole.VIEWER],
        "disabled": False,
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database."""
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        token_data = TokenData(
            username=username,
            roles=payload.get("roles", []),
            exp=payload.get("exp")
        )
    except JWTError:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    
    if user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        roles=user.roles,
        disabled=user.disabled
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


class RoleChecker:
    """Dependency for checking user roles."""
    
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, user: User = Depends(get_current_active_user)) -> User:
        """Check if user has required role."""
        user_roles = set(user.roles)
        allowed_roles = set(self.allowed_roles)
        
        # Admin has access to everything
        if UserRole.ADMIN in user_roles:
            return user
        
        if not user_roles.intersection(allowed_roles):
            logger.warning(
                "Access denied",
                username=user.username,
                user_roles=[r.value for r in user.roles],
                required_roles=[r.value for r in self.allowed_roles]
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {[r.value for r in self.allowed_roles]}"
            )
        
        return user


def require_roles(*roles: UserRole):
    """Decorator to require specific roles."""
    return Depends(RoleChecker(list(roles)))


# Convenience role checkers
require_admin = require_roles(UserRole.ADMIN)
require_manager = require_roles(UserRole.ADMIN, UserRole.MANAGER)
require_sales = require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.SALES)
require_technical = require_roles(UserRole.ADMIN, UserRole.TECHNICAL)
