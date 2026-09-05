"""Central deny-by-default policy for Phase E online object authorization."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from explore.online.models import (
    AssuranceLevel,
    CohortMembership,
    CohortRole,
    HumanPrincipal,
    NamespacePermission,
    PackageVersionIdentity,
    ServicePrincipal,
)
from explore.packages.policy import is_valid_identifier


class AuthorizationAction(StrEnum):
    """Owner-approved Phase E authorization-matrix actions."""

    SUBMIT = "submit"
    REVIEW = "review"
    APPROVE = "approve"
    REVOKE = "revoke"
    REGISTRY_READ = "registry-read"
    PIN = "pin"
    CONFIGURE = "configure"


class AuthorizationDecisionCode(StrEnum):
    """Stable internal policy outcomes; APIs must not leak object existence."""

    ALLOWED = "ALLOWED"
    DENY_BY_DEFAULT = "DENY_BY_DEFAULT"
    RESOURCE_INVALID = "RESOURCE_INVALID"
    MEMBERSHIP_REQUIRED = "MEMBERSHIP_REQUIRED"
    PRIVILEGED_ASSURANCE_REQUIRED = "PRIVILEGED_ASSURANCE_REQUIRED"
    NAMESPACE_GRANT_REQUIRED = "NAMESPACE_GRANT_REQUIRED"
    ROLE_FORBIDDEN = "ROLE_FORBIDDEN"
    SELF_APPROVAL_FORBIDDEN = "SELF_APPROVAL_FORBIDDEN"
    APPROVED_VERSION_REQUIRED = "APPROVED_VERSION_REQUIRED"
    VERSION_REVOKED = "VERSION_REVOKED"
    EXACT_SERVICE_GRANT_REQUIRED = "EXACT_SERVICE_GRANT_REQUIRED"
    EXACT_VERSION_REQUIRED = "EXACT_VERSION_REQUIRED"
    RESOURCE_INACTIVE = "RESOURCE_INACTIVE"


@dataclass(frozen=True)
class AuthorizationResource:
    """Trusted server-loaded attributes for one authorization decision.

    Online handlers must construct this object from authoritative persistence,
    never from client-supplied owner, cohort, approval, or revocation fields.
    """

    cohort_id: str
    package_id: str | None = None
    package_version: PackageVersionIdentity | None = None
    owner_actor_id: str | None = None
    submitted_by_actor_id: str | None = None
    active: bool = True
    approved: bool = False
    revoked: bool = False

    def __post_init__(self) -> None:
        if not is_valid_identifier(self.cohort_id):
            raise ValueError("cohort_id must be a valid lower-kebab-case identifier")
        if self.package_id is not None and not is_valid_identifier(self.package_id):
            raise ValueError("package_id must be a valid lower-kebab-case identifier")
        if self.package_version is not None and (
            self.package_id is None or self.package_version.package_id != self.package_id
        ):
            raise ValueError("package_version must match package_id")
        for field, value in (
            ("owner_actor_id", self.owner_actor_id),
            ("submitted_by_actor_id", self.submitted_by_actor_id),
        ):
            if value is not None:
                try:
                    parsed = UUID(value)
                except (TypeError, ValueError) as error:
                    raise ValueError(f"{field} must be a canonical UUID") from error
                if str(parsed) != value:
                    raise ValueError(f"{field} must be a canonical lowercase UUID")
        if not all(isinstance(value, bool) for value in (self.active, self.approved, self.revoked)):
            raise ValueError("active, approved, and revoked must be bool values")
        if self.revoked and not self.approved:
            raise ValueError("a revoked version must retain its historical approval state")


@dataclass(frozen=True)
class AuthorizationDecision:
    """One auditable policy result."""

    allowed: bool
    code: AuthorizationDecisionCode


_ALLOW = AuthorizationDecision(True, AuthorizationDecisionCode.ALLOWED)


def _deny(code: AuthorizationDecisionCode) -> AuthorizationDecision:
    return AuthorizationDecision(False, code)


def _active_membership(
    principal: HumanPrincipal,
    cohort_id: str,
) -> CohortMembership | None:
    return next(
        (
            membership
            for membership in principal.memberships
            if membership.cohort_id == cohort_id and membership.active
        ),
        None,
    )


def _has_submit_grant(principal: HumanPrincipal, resource: AuthorizationResource) -> bool:
    if resource.package_id is None:
        return False
    if resource.owner_actor_id == principal.actor_id:
        return True
    return any(
        grant.cohort_id == resource.cohort_id
        and grant.package_id == resource.package_id
        and grant.permission is NamespacePermission.SUBMIT
        for grant in principal.namespace_grants
    )


def _authorize_service(
    principal: ServicePrincipal,
    action: AuthorizationAction,
    resource: AuthorizationResource,
) -> AuthorizationDecision:
    if action is not AuthorizationAction.REGISTRY_READ:
        return _deny(AuthorizationDecisionCode.ROLE_FORBIDDEN)
    if resource.package_version is None or not resource.approved:
        return _deny(AuthorizationDecisionCode.APPROVED_VERSION_REQUIRED)
    if resource.package_version not in principal.exact_registry_read_grants:
        return _deny(AuthorizationDecisionCode.EXACT_SERVICE_GRANT_REQUIRED)
    return _ALLOW


def authorize(
    principal: HumanPrincipal | ServicePrincipal,
    action: AuthorizationAction,
    resource: AuthorizationResource,
) -> AuthorizationDecision:
    """Evaluate the complete approved matrix and deny every unlisted case.

    The caller must load both principal and resource attributes from trusted
    server-side persistence. Identifier secrecy is never part of this policy.
    """
    if not isinstance(action, AuthorizationAction) or not isinstance(
        resource, AuthorizationResource
    ):
        return _deny(AuthorizationDecisionCode.RESOURCE_INVALID)
    if isinstance(principal, ServicePrincipal):
        return _authorize_service(principal, action, resource)
    if not isinstance(principal, HumanPrincipal):
        return _deny(AuthorizationDecisionCode.DENY_BY_DEFAULT)

    membership = _active_membership(principal, resource.cohort_id)
    if membership is None:
        return _deny(AuthorizationDecisionCode.MEMBERSHIP_REQUIRED)
    role = membership.role
    if (
        role in (CohortRole.TEACHER, CohortRole.COURSE_ADMIN)
        and principal.assurance is not AssuranceLevel.AAL2
    ):
        return _deny(AuthorizationDecisionCode.PRIVILEGED_ASSURANCE_REQUIRED)

    if action is AuthorizationAction.SUBMIT:
        if not resource.active:
            return _deny(AuthorizationDecisionCode.RESOURCE_INACTIVE)
        if not _has_submit_grant(principal, resource):
            return _deny(AuthorizationDecisionCode.NAMESPACE_GRANT_REQUIRED)
        return _ALLOW

    if action is AuthorizationAction.REVIEW:
        if resource.package_version is None:
            return _deny(AuthorizationDecisionCode.EXACT_VERSION_REQUIRED)
        if role not in (CohortRole.TEACHER, CohortRole.COURSE_ADMIN):
            return _deny(AuthorizationDecisionCode.ROLE_FORBIDDEN)
        return _ALLOW

    if action is AuthorizationAction.APPROVE:
        if (
            resource.package_version is None
            or resource.owner_actor_id is None
            or resource.submitted_by_actor_id is None
        ):
            return _deny(AuthorizationDecisionCode.EXACT_VERSION_REQUIRED)
        if role not in (CohortRole.TEACHER, CohortRole.COURSE_ADMIN):
            return _deny(AuthorizationDecisionCode.ROLE_FORBIDDEN)
        if principal.actor_id in (resource.owner_actor_id, resource.submitted_by_actor_id):
            return _deny(AuthorizationDecisionCode.SELF_APPROVAL_FORBIDDEN)
        return _ALLOW

    if action is AuthorizationAction.REVOKE:
        if resource.package_version is None:
            return _deny(AuthorizationDecisionCode.EXACT_VERSION_REQUIRED)
        if role is not CohortRole.COURSE_ADMIN:
            return _deny(AuthorizationDecisionCode.ROLE_FORBIDDEN)
        return _ALLOW

    if action is AuthorizationAction.REGISTRY_READ:
        if role in (CohortRole.TEACHER, CohortRole.COURSE_ADMIN):
            return _ALLOW
        if resource.owner_actor_id == principal.actor_id or resource.approved:
            return _ALLOW
        return _deny(AuthorizationDecisionCode.ROLE_FORBIDDEN)

    if action is AuthorizationAction.PIN:
        if role not in (CohortRole.TEACHER, CohortRole.COURSE_ADMIN):
            return _deny(AuthorizationDecisionCode.ROLE_FORBIDDEN)
        if resource.package_version is None:
            return _deny(AuthorizationDecisionCode.EXACT_VERSION_REQUIRED)
        if not resource.approved:
            return _deny(AuthorizationDecisionCode.APPROVED_VERSION_REQUIRED)
        if resource.revoked:
            return _deny(AuthorizationDecisionCode.VERSION_REVOKED)
        return _ALLOW

    if action is AuthorizationAction.CONFIGURE:
        if role is not CohortRole.COURSE_ADMIN:
            return _deny(AuthorizationDecisionCode.ROLE_FORBIDDEN)
        return _ALLOW

    return _deny(AuthorizationDecisionCode.DENY_BY_DEFAULT)
