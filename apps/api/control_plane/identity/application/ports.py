from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from control_plane.identity.domain.types import (
    InvitationStatus,
    MembershipStatus,
    PrincipalType,
    UserStatus,
)


@dataclass(frozen=True, slots=True)
class UserRecord:
    id: uuid.UUID
    email: str
    password_hash: str
    status: UserStatus


@dataclass(frozen=True, slots=True)
class RoleRecord:
    id: uuid.UUID
    namespace: str
    slug: str
    display_name: str
    is_system: bool


@dataclass(frozen=True, slots=True)
class PermissionRecord:
    id: uuid.UUID
    namespace: str
    code: str
    description: str
    is_sensitive: bool


@dataclass(frozen=True, slots=True)
class MembershipRecord:
    id: uuid.UUID
    user_id: uuid.UUID
    principal_type: PrincipalType
    role: str  # slug — preserved for backward compatibility
    tenant_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    status: MembershipStatus
    role_id: uuid.UUID | None = None  # FK to identity_roles; None only for legacy / unmigrated rows


@dataclass(frozen=True, slots=True)
class InvitationRecord:
    id: uuid.UUID
    email: str
    principal_type: PrincipalType
    role: str  # slug — preserved for backward compatibility
    tenant_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    token_hash: str
    status: InvitationStatus
    expires_at: datetime
    invited_by_id: uuid.UUID | None
    role_id: uuid.UUID | None = None  # FK to identity_roles; None only for legacy rows


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> UserRecord | None: ...
    def get_by_id(self, user_id: uuid.UUID) -> UserRecord | None: ...
    def list_by_ids(self, user_ids: list[uuid.UUID]) -> list[UserRecord]: ...
    def create(self, user: UserRecord) -> None: ...
    def update_status(self, user_id: uuid.UUID, status: UserStatus) -> None: ...


class MembershipRepository(Protocol):
    def get_for_user(self, user_id: uuid.UUID) -> MembershipRecord | None: ...
    def has_platform(self, user_id: uuid.UUID) -> bool: ...
    def has_tenant(self, user_id: uuid.UUID) -> bool: ...
    def create(self, membership: MembershipRecord) -> None: ...
    def list_for_scope(
        self,
        *,
        principal_type: PrincipalType,
        tenant_id: uuid.UUID | None,
        customer_id: uuid.UUID | None,
    ) -> list[MembershipRecord]: ...
    def update_status(self, membership_id: uuid.UUID, status: MembershipStatus) -> None: ...


class InvitationRepository(Protocol):
    def get_by_token_hash(self, token_hash: str) -> InvitationRecord | None: ...
    def create(self, invitation: InvitationRecord) -> None: ...
    def mark_accepted(self, invitation_id: uuid.UUID) -> None: ...
    def list_open_for_email(self, email: str) -> list[InvitationRecord]: ...
    def list_for_scope(
        self,
        *,
        principal_type: PrincipalType,
        tenant_id: uuid.UUID | None,
        customer_id: uuid.UUID | None,
    ) -> list[InvitationRecord]: ...


class RoleRepository(Protocol):
    def get_by_slug(self, slug: str) -> RoleRecord | None: ...
    def get_by_id(self, role_id: uuid.UUID) -> RoleRecord | None: ...
    def list_permissions(self, role_id: uuid.UUID) -> frozenset[str]: ...


class PermissionRepository(Protocol):
    def get_by_code(self, namespace: str, code: str) -> PermissionRecord | None: ...
    def list_for_namespace(self, namespace: str) -> list[PermissionRecord]: ...


class PasswordHasher(Protocol):
    def hash(self, raw: str) -> str: ...
    def verify(self, raw: str, encoded: str) -> bool: ...


class SessionGateway(Protocol):
    def create(self, user_id: uuid.UUID) -> str: ...
    def destroy_current(self) -> None: ...
    def destroy_all(self, user_id: uuid.UUID) -> int: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class LoginRateLimiter(Protocol):
    def allow(self, key: str) -> bool: ...
    def register_failure(self, key: str) -> None: ...
    def reset(self, key: str) -> None: ...
