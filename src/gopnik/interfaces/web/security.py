"""
Web security and cleanup utilities.

Implements security measures, rate limiting, and automatic cleanup for the web interface.
"""

import os
import time
import hashlib
import secrets
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from collections import defaultdict, deque

from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware for web requests."""
    
    def __init__(self, app, calls: int = 100, period: int = 3600):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            calls: Number of calls allowed per period
            period: Time period in seconds
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: Dict[str, deque] = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        if self._is_rate_limited(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Process request
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers (behind proxy/CDN)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited."""
        now = time.time()
        client_requests = self.clients[client_ip]
        
        # Remove old requests outside the time window
        while client_requests and client_requests[0] < now - self.period:
            client_requests.popleft()
        
        # Check if limit exceeded
        if len(client_requests) >= self.calls:
            return True
        
        # Add current request
        client_requests.append(now)
        return False


class SecurityHeaders:
    """Security headers for web responses."""
    
    @staticmethod
    def add_security_headers(response: Response) -> Response:
        """Add security headers to response."""
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Other security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS (only for HTTPS)
        if response.headers.get("X-Forwarded-Proto") == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class SessionManager:
    """Simple session management for web interface."""
    
    def __init__(self, session_timeout: int = 3600):
        """
        Initialize session manager.
        
        Args:
            session_timeout: Session timeout in seconds
        """
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = session_timeout
    
    def create_session(self, client_ip: str) -> str:
        """Create a new session."""
        session_id = secrets.token_urlsafe(32)
        
        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "client_ip": client_ip,
            "jobs": []
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data."""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if session expired
        if datetime.now() - session["last_accessed"] > timedelta(seconds=self.session_timeout):
            del self.sessions[session_id]
            return None
        
        # Update last accessed
        session["last_accessed"] = datetime.now()
        return session
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if now - session["last_accessed"] > timedelta(seconds=self.session_timeout):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")


class SecureFileHandler:
    """Secure file handling utilities."""
    
    @staticmethod
    def secure_filename(filename: str) -> str:
        """Generate a secure filename."""
        # Remove path components
        filename = os.path.basename(filename)
        
        # Generate hash-based filename
        timestamp = str(int(time.time()))
        random_suffix = secrets.token_hex(8)
        file_ext = Path(filename).suffix.lower()
        
        # Validate extension
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif'}
        if file_ext not in allowed_extensions:
            raise ValueError(f"File extension {file_ext} not allowed")
        
        return f"{timestamp}_{random_suffix}{file_ext}"
    
    @staticmethod
    def secure_delete(file_path: Path, passes: int = 3):
        """Securely delete a file by overwriting it multiple times."""
        if not file_path.exists():
            return
        
        try:
            file_size = file_path.stat().st_size
            
            with open(file_path, "r+b") as f:
                for _ in range(passes):
                    # Overwrite with random data
                    f.seek(0)
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())
            
            # Finally delete the file
            file_path.unlink()
            logger.info(f"Securely deleted file: {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to securely delete {file_path}: {str(e)}")
            # Fallback to regular deletion
            try:
                file_path.unlink()
            except Exception:
                pass
    
    @staticmethod
    def validate_file_content(file_path: Path, expected_type: str) -> bool:
        """Validate file content matches expected type."""
        try:
            with open(file_path, "rb") as f:
                header = f.read(1024)  # Read first 1KB
            
            # Basic file type validation based on magic bytes
            if expected_type == "application/pdf":
                return header.startswith(b"%PDF-")
            elif expected_type in ["image/png"]:
                return header.startswith(b"\x89PNG\r\n\x1a\n")
            elif expected_type in ["image/jpeg"]:
                return header.startswith(b"\xff\xd8\xff")
            elif expected_type in ["image/tiff"]:
                return header.startswith(b"II*\x00") or header.startswith(b"MM\x00*")
            
            return True  # Allow other types for now
            
        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return False


class CloudflareIntegration:
    """Cloudflare integration utilities."""
    
    @staticmethod
    def is_cloudflare_request(request: Request) -> bool:
        """Check if request is coming through Cloudflare."""
        cf_headers = [
            "CF-Ray",
            "CF-Connecting-IP",
            "CF-IPCountry",
            "CF-Visitor"
        ]
        
        return any(header in request.headers for header in cf_headers)
    
    @staticmethod
    def get_real_ip(request: Request) -> str:
        """Get real client IP from Cloudflare headers."""
        # Cloudflare provides the real IP in CF-Connecting-IP
        cf_ip = request.headers.get("CF-Connecting-IP")
        if cf_ip:
            return cf_ip
        
        # Fallback to standard headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        return request.client.host if request.client else "unknown"
    
    @staticmethod
    def get_country_code(request: Request) -> Optional[str]:
        """Get country code from Cloudflare headers."""
        return request.headers.get("CF-IPCountry")


class WebSecurityManager:
    """Main security manager for web interface."""
    
    def __init__(self):
        self.session_manager = SessionManager()
        self.blocked_ips: set = set()
        self.suspicious_activity: Dict[str, List[datetime]] = defaultdict(list)
    
    def check_request_security(self, request: Request) -> bool:
        """Perform security checks on incoming request."""
        client_ip = CloudflareIntegration.get_real_ip(request)
        
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Check for suspicious activity
        if self._is_suspicious_activity(client_ip, request):
            self._log_suspicious_activity(client_ip, request)
        
        return True
    
    def _is_suspicious_activity(self, client_ip: str, request: Request) -> bool:
        """Check for suspicious activity patterns."""
        # Check for common attack patterns in URL
        suspicious_patterns = [
            "../", "..\\", "<script", "javascript:", "vbscript:",
            "onload=", "onerror=", "eval(", "document.cookie",
            "union select", "drop table", "insert into"
        ]
        
        url_path = str(request.url.path).lower()
        query_params = str(request.url.query).lower()
        
        for pattern in suspicious_patterns:
            if pattern in url_path or pattern in query_params:
                return True
        
        return False
    
    def _log_suspicious_activity(self, client_ip: str, request: Request):
        """Log suspicious activity."""
        now = datetime.now()
        self.suspicious_activity[client_ip].append(now)
        
        # Clean old entries (keep last 24 hours)
        cutoff = now - timedelta(hours=24)
        self.suspicious_activity[client_ip] = [
            timestamp for timestamp in self.suspicious_activity[client_ip]
            if timestamp > cutoff
        ]
        
        # Block IP if too many suspicious activities
        if len(self.suspicious_activity[client_ip]) > 10:
            self.blocked_ips.add(client_ip)
            logger.warning(f"Blocked IP due to suspicious activity: {client_ip}")
        
        logger.warning(
            f"Suspicious activity from {client_ip}: "
            f"{request.method} {request.url.path}"
        )


# Global security manager instance
security_manager = WebSecurityManager()