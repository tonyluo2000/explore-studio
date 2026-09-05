"""Opaque server-side staff session lifecycle and CSRF verification."""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from explore.online.models import AssuranceLevel
from explore.online.submission_models import AuthenticatedOIDCIdentity
from explore.online.transport_models import StaffSession, StaffTransportConfig
from explore.online.transport_persistence import SQLiteStaffTransportStore

_OPAQUE_TOKEN = re.compile(r"[A-Za-z0-9_-]{43,512}", re.ASCII)


class SessionAuthenticationError(PermissionError):
    """The opaque session is missing, expired, revoked, or no longer authorized."""


class CSRFValidationError(PermissionError):
    """A state-changing request lacks its session-bound CSRF proof."""


@dataclass(frozen=True)
class CreatedStaffSession:
    session_token: str
    csrf_token: str
    session: StaffSession


@dataclass(frozen=True)
class AuthenticatedStaffSession:
    identity: AuthenticatedOIDCIdentity
    session: StaffSession


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class StaffSessionManager:
    def __init__(
        self,
        store: SQLiteStaffTransportStore,
        config: StaffTransportConfig,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        token_factory: Callable[[int], str] = secrets.token_urlsafe,
    ) -> None:
        self._store = store
        self._config = config
        self._clock = clock
        self._token_factory = token_factory

    def create(self, identity: AuthenticatedOIDCIdentity) -> CreatedStaffSession:
        now = self._clock()
        if self._store.identity_provider_assurance(identity.issuer) is not AssuranceLevel.AAL2:
            raise SessionAuthenticationError("staff authentication was rejected")
        actor = self._store.resolve_federated_actor(identity.issuer, identity.subject)
        if actor is None or not self._store.actor_is_current_staff(actor.actor_id, now=now):
            raise SessionAuthenticationError("staff authentication was rejected")
        session_token = self._token_factory(32)
        csrf_token = self._token_factory(32)
        if (
            not isinstance(session_token, str)
            or _OPAQUE_TOKEN.fullmatch(session_token) is None
            or not isinstance(csrf_token, str)
            or _OPAQUE_TOKEN.fullmatch(csrf_token) is None
            or session_token == csrf_token
        ):
            raise RuntimeError("trusted token factory returned invalid session material")
        absolute_expires_at = now + self._config.session_absolute_ttl
        session = StaffSession(
            session_digest=_digest(session_token),
            actor_id=actor.actor_id,
            issuer=identity.issuer,
            subject=identity.subject,
            assurance=identity.assurance,
            csrf_digest=_digest(csrf_token),
            created_at=now,
            idle_expires_at=min(now + self._config.session_idle_ttl, absolute_expires_at),
            absolute_expires_at=absolute_expires_at,
            last_seen_at=now,
        )
        if not self._store.append_staff_session(session):
            raise SessionAuthenticationError("staff authentication was rejected")
        return CreatedStaffSession(session_token, csrf_token, session)

    def authenticate(self, session_token: str | None) -> AuthenticatedStaffSession:
        if not isinstance(session_token, str) or _OPAQUE_TOKEN.fullmatch(session_token) is None:
            raise SessionAuthenticationError("staff authentication is required")
        now = self._clock()
        session = self._store.load_active_staff_session(
            session_digest=_digest(session_token),
            now=now,
            idle_ttl=self._config.session_idle_ttl,
        )
        if session is None:
            raise SessionAuthenticationError("staff authentication is required")
        actor = self._store.resolve_federated_actor(session.issuer, session.subject)
        if (
            actor is None
            or actor.actor_id != session.actor_id
            or self._store.identity_provider_assurance(session.issuer) is not AssuranceLevel.AAL2
            or not self._store.actor_is_current_staff(session.actor_id, now=now)
        ):
            self._store.revoke_staff_session(session_digest=session.session_digest, now=now)
            raise SessionAuthenticationError("staff authentication is required")
        return AuthenticatedStaffSession(
            identity=AuthenticatedOIDCIdentity(
                session.issuer,
                session.subject,
                session.assurance,
            ),
            session=session,
        )

    @staticmethod
    def require_aal2(authenticated: AuthenticatedStaffSession) -> None:
        if authenticated.identity.assurance is not AssuranceLevel.AAL2:
            raise SessionAuthenticationError("AAL2 authentication is required")

    @staticmethod
    def verify_csrf(authenticated: AuthenticatedStaffSession, csrf_token: str | None) -> None:
        if (
            not isinstance(csrf_token, str)
            or _OPAQUE_TOKEN.fullmatch(csrf_token) is None
            or not hmac.compare_digest(_digest(csrf_token), authenticated.session.csrf_digest)
        ):
            raise CSRFValidationError("CSRF validation failed")

    def revoke(self, authenticated: AuthenticatedStaffSession) -> None:
        self._store.revoke_staff_session(
            session_digest=authenticated.session.session_digest,
            now=self._clock(),
        )


__all__ = [
    "AuthenticatedStaffSession",
    "CSRFValidationError",
    "CreatedStaffSession",
    "SessionAuthenticationError",
    "StaffSessionManager",
]
