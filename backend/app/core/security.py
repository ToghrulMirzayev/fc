"""Security primitives.

- Passwords: Argon2id (memory-hard, current best practice).
- Access tokens: JWT (HS256), short TTL.
- Refresh tokens: opaque random strings, stored hashed.
- QR tokens: HMAC-signed payloads with member_id + nonce + expiry.

QR tokens use a separate signing key (QR_SIGNING_KEY) so it can rotate
independently of SECRET_KEY without invalidating user sessions.
"""

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

# Argon2id with sensible defaults. Tune via env if needed later.
_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        _hasher.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False


# ─────────────────────────────────────────────────────────────────
# JWT access tokens
# ─────────────────────────────────────────────────────────────────


def create_access_token(
    user_id: UUID, tenant_id: UUID | None, role: str
) -> str:
    """Issue a short-lived access token. Subject is the user UUID."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "tid": str(tenant_id) if tenant_id else None,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(minutes=settings.ACCESS_TOKEN_TTL_MIN)).timestamp()
        ),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    """Returns the claims dict. Raises jwt.PyJWTError on bad/expired."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


# ─────────────────────────────────────────────────────────────────
# Refresh tokens
# ─────────────────────────────────────────────────────────────────


def generate_refresh_token() -> tuple[str, str]:
    """Return (raw_token, hash). Store the hash, return the raw to client."""
    raw = secrets.token_urlsafe(48)
    h = hashlib.sha256(raw.encode()).hexdigest()
    return raw, h


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


# ─────────────────────────────────────────────────────────────────
# QR tokens — used by Telegram bot and check-in scanner
# ─────────────────────────────────────────────────────────────────


def make_qr_token(member_id: UUID, tenant_id: UUID) -> tuple[str, str]:
    """Create a short-lived signed QR token.

    Returns (token, nonce). The nonce is also stored in Redis with TTL
    so the same token can be redeemed at most once. The token itself
    embeds nonce + expiry, so the scanner can validate without a DB hit
    until the very last step (Redis SETNX to burn the nonce).
    """
    now = datetime.now(UTC)
    expires_at = int(
        (now + timedelta(seconds=settings.QR_TOKEN_TTL_SECONDS)).timestamp()
    )
    nonce = secrets.token_urlsafe(12)
    # Payload: member_id|tenant_id|expires_at|nonce
    payload = f"{member_id}|{tenant_id}|{expires_at}|{nonce}"
    sig = hmac.new(
        settings.QR_SIGNING_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    token = f"{payload}|{sig}"
    return token, nonce


def verify_qr_token(token: str) -> tuple[UUID, UUID, str] | None:
    """Verify a QR token. Returns (member_id, tenant_id, nonce) or None
    if invalid/expired.

    Caller MUST then check the nonce against Redis to enforce single-use.
    """
    try:
        member_id_s, tenant_id_s, expires_s, nonce, sig = token.split("|")
    except ValueError:
        return None

    payload = f"{member_id_s}|{tenant_id_s}|{expires_s}|{nonce}"
    expected_sig = hmac.new(
        settings.QR_SIGNING_KEY.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected_sig, sig):
        return None

    try:
        expires_at = int(expires_s)
    except ValueError:
        return None
    if datetime.now(UTC).timestamp() > expires_at:
        return None

    try:
        return UUID(member_id_s), UUID(tenant_id_s), nonce
    except ValueError:
        return None
