import time
import re
import logging
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger("BotShield")

# Known malicious bot User-Agent signatures and security vulnerability scanners
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

# Honeypot paths: legitimate enterprise users never hit these; scanners probing them get banned
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
    "/.aws/credentials",
}


class SlidingWindowRateLimiter:
    """
    High-performance in-memory sliding-window rate limiter with burst mitigation,
    per-minute quotas, and automatic defensive IP bans.
    """

    def __init__(self, limit_per_minute: int = 60, burst_limit_per_sec: int = 8):
        self.limit_per_minute = limit_per_minute
        self.burst_limit_per_sec = burst_limit_per_sec
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.banned_ips: Dict[str, float] = {}

    def is_banned(self, ip: str) -> bool:
        if ip in self.banned_ips:
            if time.time() < self.banned_ips[ip]:
                return True
            del self.banned_ips[ip]
        return False

    def ban(self, ip: str, duration_seconds: int = 300):
        self.banned_ips[ip] = time.time() + duration_seconds
        logger.warning(f"🚫 IP {ip} blacklisted for {duration_seconds}s (threat detected).")

    def allow(self, ip: str) -> Tuple[bool, str]:
        now = time.time()

        if self.is_banned(ip):
            remaining = int(self.banned_ips[ip] - now)
            return False, f"IP is temporarily blacklisted by BotShield. Retry in {remaining}s."

        timestamps = self.requests[ip]
        cutoff = now - 60.0
        self.requests[ip] = [t for t in timestamps if t > cutoff]
        timestamps = self.requests[ip]

        # Check burst in the last 1 second
        burst_cutoff = now - 1.0
        recent_burst = sum(1 for t in timestamps if t > burst_cutoff)
        if recent_burst >= self.burst_limit_per_sec:
            logger.warning(f"⚠️ Burst tripped for IP {ip}: {recent_burst} req/s.")
            return False, "Rate limit exceeded (burst protection triggered)."

        # Check sliding minute limit
        if len(timestamps) >= self.limit_per_minute:
            logger.warning(f"⚠️ Rate limit exceeded for IP {ip}: {len(timestamps)}/min.")
            return False, "Rate limit exceeded (per-minute quota reached)."

        timestamps.append(now)
        return True, "OK"


class SecurityStats:
    def __init__(self):
        self.total_scans_blocked = 0
        self.honeypot_triggers = 0
        self.rate_limits_enforced = 0
        self.active_bans = 0

    def to_dict(self):
        return {
            "status": "operational",
            "shield": "BotShield WAF v2.0",
            "total_scans_blocked": self.total_scans_blocked,
            "honeypot_triggers": self.honeypot_triggers,
            "rate_limits_enforced": self.rate_limits_enforced,
            "active_bans": self.active_bans,
        }


bot_shield_stats = SecurityStats()
rate_limiter = SlidingWindowRateLimiter(limit_per_minute=60, burst_limit_per_sec=8)


class BotShieldMiddleware(BaseHTTPMiddleware):
    """
    Principal Engineer grade WAF middleware:
    - Zero-tolerance honeypot traps for proactive bot blacklisting
    - Scanner User-Agent signature drops
    - Sliding-window rate limiter
    - Defensive enterprise response headers
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract client IP supporting proxy headers
        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.client.host
            if request.client
            else "unknown"
        )
        user_agent = request.headers.get("User-Agent", "")
        request_path = request.url.path

        # 1. HONEYPOT TRAP CHECK
        if request_path in HONEYPOT_PATHS:
            rate_limiter.ban(client_ip, duration_seconds=600)
            bot_shield_stats.honeypot_triggers += 1
            bot_shield_stats.active_bans = len(rate_limiter.banned_ips)
            logger.critical(f"🍯 Honeypot triggered by {client_ip} on '{request_path}'. Banned for 10m.")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Forbidden",
                    "code": "BOTSHIELD_HONEYPOT_TRIP",
                    "message": "Automated security scanning prohibited.",
                },
            )

        # 2. MALICIOUS SCANNER USER-AGENT CHECK
        for pattern in SUSPICIOUS_UA_PATTERNS:
            if pattern.search(user_agent):
                rate_limiter.ban(client_ip, duration_seconds=300)
                bot_shield_stats.total_scans_blocked += 1
                bot_shield_stats.active_bans = len(rate_limiter.banned_ips)
                logger.warning(f"🚫 Blocked scanner UA '{user_agent}' from {client_ip}.")
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "Forbidden",
                        "code": "BOTSHIELD_SCANNER_DETECTED",
                        "message": "Security scanner signature detected.",
                    },
                )

        # 3. RATE LIMITING (Skip static/docs assets)
        if not (request_path.startswith("/docs") or request_path.startswith("/openapi.json") or request_path == "/health"):
            allowed, reason = rate_limiter.allow(client_ip)
            if not allowed:
                bot_shield_stats.rate_limits_enforced += 1
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "Too Many Requests",
                        "code": "BOTSHIELD_RATE_LIMIT",
                        "message": reason,
                    },
                    headers={"Retry-After": "60"},
                )

        # 4. EXECUTE PIPELINE
        response = await call_next(request)

        # 5. ATTACH ENTERPRISE DEFENSIVE HEADERS
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["X-BotShield-Status"] = "protected"

        return response
