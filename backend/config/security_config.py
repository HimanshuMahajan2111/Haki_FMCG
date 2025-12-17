"""
Security Hardening Configuration
"""
from typing import List, Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import secrets
import hashlib


class SecurityConfig:
    """Security configuration and utilities"""
    
    # Password requirements
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True
    
    # Session configuration
    SESSION_TIMEOUT_MINUTES = 60
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    
    # API rate limiting
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW_SECONDS = 60
    
    # Token configuration
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # CORS configuration
    ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://yourdomain.com"
    ]
    
    # Security headers
    SECURITY_HEADERS = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": "default-src 'self'",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, List[str]]:
        """Validate password strength"""
        errors = []
        
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters")
        
        if SecurityConfig.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if SecurityConfig.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if SecurityConfig.REQUIRE_DIGIT and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if SecurityConfig.REQUIRE_SPECIAL and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)
        
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # iterations
        )
        
        return hashed.hex(), salt
    
    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """Verify password against hash"""
        new_hash, _ = SecurityConfig.hash_password(password, salt)
        return secrets.compare_digest(new_hash, hashed)
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)


class IPWhitelist:
    """IP whitelist for sensitive endpoints"""
    
    def __init__(self, allowed_ips: List[str]):
        self.allowed_ips = set(allowed_ips)
    
    def is_allowed(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        return ip in self.allowed_ips or ip == "127.0.0.1"
    
    def add_ip(self, ip: str):
        """Add IP to whitelist"""
        self.allowed_ips.add(ip)
    
    def remove_ip(self, ip: str):
        """Remove IP from whitelist"""
        self.allowed_ips.discard(ip)


class RequestValidator:
    """Validate and sanitize incoming requests"""
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Sanitize user input"""
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Limit length
        max_length = 10000
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    def validate_file_upload(filename: str, content_type: str, size: int) -> tuple[bool, Optional[str]]:
        """Validate file upload"""
        # Allowed extensions
        allowed_extensions = {'.pdf', '.doc', '.docx', '.txt', '.xls', '.xlsx'}
        
        # Check extension
        ext = filename[filename.rfind('.'):].lower() if '.' in filename else ''
        if ext not in allowed_extensions:
            return False, f"File type not allowed. Allowed types: {', '.join(allowed_extensions)}"
        
        # Check size (max 10MB)
        max_size = 10 * 1024 * 1024
        if size > max_size:
            return False, f"File too large. Maximum size: {max_size // (1024*1024)}MB"
        
        # Validate content type
        allowed_content_types = {
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        if content_type not in allowed_content_types:
            return False, "Invalid content type"
        
        return True, None
    
    @staticmethod
    def detect_sql_injection(text: str) -> bool:
        """Detect potential SQL injection attempts"""
        sql_keywords = [
            'union', 'select', 'insert', 'update', 'delete',
            'drop', 'create', 'alter', 'exec', 'execute',
            'script', '--', '/*', '*/', 'xp_', 'sp_'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in sql_keywords)
    
    @staticmethod
    def detect_xss(text: str) -> bool:
        """Detect potential XSS attempts"""
        xss_patterns = [
            '<script', 'javascript:', 'onerror=',
            'onload=', 'onclick=', '<iframe'
        ]
        
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in xss_patterns)


# Login attempt tracking
class LoginAttemptTracker:
    """Track failed login attempts"""
    
    def __init__(self):
        self.attempts = {}  # {username: [(timestamp, ip), ...]}
        self.locked_accounts = {}  # {username: lockout_until}
    
    def record_attempt(self, username: str, ip: str, success: bool):
        """Record login attempt"""
        if success:
            # Clear attempts on successful login
            if username in self.attempts:
                del self.attempts[username]
            if username in self.locked_accounts:
                del self.locked_accounts[username]
        else:
            # Record failed attempt
            if username not in self.attempts:
                self.attempts[username] = []
            
            self.attempts[username].append((datetime.utcnow(), ip))
            
            # Check if account should be locked
            recent_attempts = [
                (ts, ip) for ts, ip in self.attempts[username]
                if datetime.utcnow() - ts < timedelta(minutes=30)
            ]
            
            if len(recent_attempts) >= SecurityConfig.MAX_LOGIN_ATTEMPTS:
                lockout_until = datetime.utcnow() + timedelta(
                    minutes=SecurityConfig.LOCKOUT_DURATION_MINUTES
                )
                self.locked_accounts[username] = lockout_until
    
    def is_locked(self, username: str) -> tuple[bool, Optional[datetime]]:
        """Check if account is locked"""
        if username in self.locked_accounts:
            lockout_until = self.locked_accounts[username]
            
            if datetime.utcnow() < lockout_until:
                return True, lockout_until
            else:
                # Lockout expired
                del self.locked_accounts[username]
        
        return False, None
    
    def get_remaining_attempts(self, username: str) -> int:
        """Get remaining login attempts"""
        if username not in self.attempts:
            return SecurityConfig.MAX_LOGIN_ATTEMPTS
        
        recent_attempts = [
            ts for ts, ip in self.attempts[username]
            if datetime.utcnow() - ts < timedelta(minutes=30)
        ]
        
        return max(0, SecurityConfig.MAX_LOGIN_ATTEMPTS - len(recent_attempts))


# Global instances
_login_tracker = None
_ip_whitelist = None

def get_login_tracker() -> LoginAttemptTracker:
    """Get global login attempt tracker"""
    global _login_tracker
    if _login_tracker is None:
        _login_tracker = LoginAttemptTracker()
    return _login_tracker

def get_ip_whitelist() -> IPWhitelist:
    """Get global IP whitelist"""
    global _ip_whitelist
    if _ip_whitelist is None:
        _ip_whitelist = IPWhitelist([
            "127.0.0.1",
            "::1"
        ])
    return _ip_whitelist
