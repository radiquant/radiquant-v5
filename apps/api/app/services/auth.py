"""Authentication service primitives.

The current restart phase only establishes secure runtime primitives. Public login,
invite, password reset, MFA, and feature routes remain intentionally blocked until
future contract phases explicitly add them.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from app.core.config import Settings, get_settings
from app.models.identity import RoleName

TOKEN_ALGORITHM = "HS256"


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    """Authenticated user identity extracted from a validated access token."""

    user_id: UUID
    tenant_id: UUID
    role: RoleName
    email: str | None = None


class AuthError(Exception):
    """Authentication failure with an HTTP-compatible status code."""

    def __init__(self, detail: str = "Authentication required", status_code: int = 401) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class AuthService:
    """Issue and verify signed access tokens for tenant-scoped users."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def _secret(self) -> str:
        return self.settings.secret_key.get_secret_value()

    def issue_access_token(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        role: RoleName,
        email: str | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a signed bearer token for a tenant-scoped principal."""
        now = datetime.now(UTC)
        ttl = expires_delta or timedelta(minutes=self.settings.access_token_ttl_minutes)
        payload: dict[str, object] = {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "role": role.value,
            "iat": int(now.timestamp()),
            "exp": int((now + ttl).timestamp()),
        }
        if email is not None:
            payload["email"] = email
        return jwt.encode(payload, self._secret, algorithm=TOKEN_ALGORITHM)

    def authenticate_bearer(self, authorization: str | None) -> AuthenticatedPrincipal:
        """Validate an Authorization header and return the authenticated principal."""
        if not authorization:
            raise AuthError()

        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            raise AuthError("Invalid authorization header")

        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[TOKEN_ALGORITHM],
                options={"require": ["sub", "tenant_id", "role", "iat", "exp"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthError("Token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthError("Invalid token") from exc

        try:
            user_id = UUID(str(payload["sub"]))
            tenant_id = UUID(str(payload["tenant_id"]))
            role = RoleName(str(payload["role"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise AuthError("Invalid token claims") from exc

        email = payload.get("email")
        return AuthenticatedPrincipal(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            email=str(email) if email is not None else None,
        )


def get_auth_service() -> AuthService:
    """FastAPI dependency for the authentication service."""
    return AuthService()
