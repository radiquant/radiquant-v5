"""Password hashing primitives for the identity core.

Uses PBKDF2-HMAC-SHA256 from the Python standard library to avoid introducing a
runtime dependency before the dependency policy is finalized.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

PASSWORD_HASH_PREFIX = "pbkdf2_sha256"
DEFAULT_ITERATIONS = 600_000
SALT_BYTES = 16


class PasswordHashError(ValueError):
    """Raised when a stored password hash is malformed."""


def hash_password(password: str, *, iterations: int = DEFAULT_ITERATIONS) -> str:
    """Return a salted password hash string for storage."""
    if not password:
        raise ValueError("password must not be empty")

    salt = secrets.token_hex(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), iterations).hex()
    return f"{PASSWORD_HASH_PREFIX}${iterations}${salt}${digest}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored hash without leaking timing details."""
    try:
        prefix, iterations_text, salt, expected = stored_hash.split("$", 3)
        if prefix != PASSWORD_HASH_PREFIX:
            raise PasswordHashError("unsupported password hash prefix")
        iterations = int(iterations_text)
    except (AttributeError, ValueError) as exc:
        raise PasswordHashError("malformed password hash") from exc

    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), iterations).hex()
    return hmac.compare_digest(actual, expected)
