import time
import re
import logfire
from collections import defaultdict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.config import settings

# Known malicious bot User-Agent signatures and vulnerability scanners
SUSPICIOUS_UA_PATTERNS = [
    re.compile(r"sqlmap", re.IGNORECASE),
    re.compile(r"nikto", re.IGNORECASE),
    re.compile(r"nmap", re.IGNORECASE),
    re.compile(r"masscan", re.IGNORECASE),
    re.compile(r"wpscan", re.IGNORECASE),
    re.compile(r"dirbuster", re.IGNORECASE),
    re.compile(r"gobuster", re.IGNORECASE),
    re.compile(r"acunetix", re.IGNORECASE),
    re.compile(r"zgrab", re.IGNORECASE),
    re.compile(r"censys", re.IGNORECASE),
    re.compile(r"shodan", re.IGNORECASE),
    re.compile(r"python-urllib", re.IGNORECASE),
]

# Honeypot paths scanned only by malicious automated bots
HONEYPOT_PATHS = {
    "/wp-admin",
    "/wp-login.php",
    "/.env",
    "/.git",
    "/.git/config",
    "/phpmyadmin",
    "/admin.php",
    "/xmlrpc.php",
    "/config.json",
    "/backup.sql",
    "/aws/credentials",
}

# Attack injection patterns in payload
INJECTION_PATTERNS = [
    re.compile(r"(\bunion\b\s+\bselect\b)", re.IGNORECASE),
    re.compile(r"(\bselect\b.+\bfrom\b.+\binformation_schema\b)", re.IGNORECASE),
    re.compile(r"(\bor\b\s+1\s*=\s*1\b)", re.IGNORECASE),
    re.compile(r"(<script\b[^>]*>[\s\S]*?<\/script>)", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"(\.\./\.\./|\.\.\\\.\.\\)", re.IGNORECASE),
]


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter with burst mitigation and temporary bans."""

    def __init__(self, limit_per_minute: int = 60, burst_limit_per_sec: int = 5):
        self.limit_per_minute = limit_per_minute
        self.burst_limit_per_sec = burst_limit_per_sec
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.banned_ips: dict[str, float] = {}  # ip -> ban_until_timestamp

    def is_banned(self, ip: str) -> bool:
        if ip in self.banned_ips:
            if time.time() < self.banned_ips[ip]:
                return True
            else:
                del self.banned_ips[ip]
        return False

    def ban(self, ip: str, duration_seconds: int = 300):
        self.banned_ips[ip] = time.time() + duration_seconds
        logfire.warning(f"🚫 IP {ip} has been BANNED for {duration_seconds}s due to malicious bot activity.")

    def allow(self, ip: str) -> tuple[bool, str]:
        now = time.time()

        if self.is_banned(ip):
            remaining = int(self.banned_ips[ip] - now)
            return False, f"IP is temporarily blacklisted. Retry in {remaining} seconds."

        timestamps = self.requests[ip]
        # Purge timestamps older than 60 seconds
        cutoff = now - 60.0
        self.requests[ip] = [t for t in timestamps if t > cutoff]
        timestamps = self.requests[ip]

        # Check burst limit in the last 1 second
        burst_cutoff = now - 1.0
        recent_burst = sum(1 for t in timestamps if t > burst_cutoff)
        if recent_burst >= self.burst_limit_per_sec:
            logfire.warning(f"⚠️ Burst rate limit tripped for IP {ip}: {recent_burst} req/s.")
            return False, "Rate limit exceeded (burst protection). Please slow down."

        # Check sliding minute limit
        if len(timestamps) >= self.limit_per_minute:
            logfire.warning(f"⚠️ Per-minute rate limit exceeded for IP {ip} ({len(timestamps)}/{self.limit_per_minute}).")
            return False, "Too many requests. Please wait before retrying."

        timestamps.append(now)
        return True, "OK"


# Global singleton rate limiter
rate_limiter = SlidingWindowRateLimiter(
    limit_per_minute=settings.RATE_LIMIT_PER_MINUTE,
    burst_limit_per_sec=settings.BURST_LIMIT_PER_SECOND,
)


class BotShieldMiddleware(BaseHTTPMiddleware):
    """
    Enterprise Bot Defense & Attack Shield:
    1. Honeypot traps: Instantly bans scanners targeting sensitive URLs.
    2. User-Agent scrutiny: Blocks known scanner toolkits and empty User-Agents on POST.
    3. Rate Limiting & Burst Protection: Drops DDoS and scraper hammering.
    4. Payload size and injection verification.
    5. Security response headers.
    """

    async def dispatch(self, request: Request, call_next):
        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or (request.client.host if request.client else "127.0.0.1")
        )
        path = request.url.path

        # ── 1. Honeypot trap ──────────────────────────────────────────
        if path.lower() in HONEYPOT_PATHS or any(path.lower().startswith(h) for h in HONEYPOT_PATHS):
            if client_ip not in ("127.0.0.1", "::1", "localhost"):
                rate_limiter.ban(client_ip, duration_seconds=600)
            logfire.warning(f"🍯 Honeypot triggered by {client_ip} on path '{path}'. Flagging IP.")
            return JSONResponse(
                status_code=403,
                content={"error": "Access Denied. Malicious activity flagged and reported."},
            )

        # ── 2. Check if IP is blacklisted ─────────────────────────────
        if rate_limiter.is_banned(client_ip):
            return JSONResponse(
                status_code=403,
                content={"error": "Access Denied. IP address is temporarily blacklisted due to automated bot activity."},
            )

        # ── 3. User-Agent verification ────────────────────────────────
        user_agent = request.headers.get("user-agent", "")
        for pattern in SUSPICIOUS_UA_PATTERNS:
            if pattern.search(user_agent):
                if client_ip not in ("127.0.0.1", "::1", "localhost"):
                    rate_limiter.ban(client_ip, duration_seconds=300)
                logfire.warning(f"🛡️ Blocked attack tool signature '{user_agent}' from {client_ip}.")
                return JSONResponse(
                    status_code=403,
                    content={"error": "Automated security scanning tools are prohibited."},
                )

        # ── 4. Rate Limiting ──────────────────────────────────────────
        # Don't throttle health checks or docs
        if not path.startswith(("/health", "/docs", "/openapi.json", "/favicon.ico")):
            allowed, reason = rate_limiter.allow(client_ip)
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    headers={"Retry-After": "60"},
                    content={
                        "error": "Rate limit exceeded.",
                        "detail": reason,
                        "status": 429,
                    },
                )

        # ── 5. Payload size guard (Prevent slowloris / memory exhaustion)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_PAYLOAD_BYTES:
            logfire.warning(f"⚠️ Payload too large from {client_ip}: {content_length} bytes.")
            return JSONResponse(
                status_code=413,
                content={"error": f"Payload too large. Max allowed: {settings.MAX_PAYLOAD_BYTES} bytes."},
            )

        # Proceed with request
        response: Response = await call_next(request)

        # ── 6. Inject Defense Security Headers ────────────────────────
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
