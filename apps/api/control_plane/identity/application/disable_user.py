from __future__ import annotations

import uuid
from dataclasses import dataclass

from control_plane.identity.application.ports import (
    MembershipRecord,
    MembershipRepository,
    SessionGateway,
    UserRepository,
)
from control_plane.identity.domain.roles import permissions_for_role
from control_plane.identity.domain.types import MembershipStatus, UserStatus
from shared_kernel.errors import DomainError


@dataclass(frozen=True, slots=True)
class DisableUserCommand:
    actor_id: uuid.UUID
    actor_membership: MembershipRecord
    target_user_id: uuid.UUID


class DisableUser:
    def __init__(
        self,
        users: UserRepository,
        memberships: MembershipRepository,
        sessions: SessionGateway,
    ) -> None:
        self._users = users
        self._memberships = memberships
        self._sessions = sessions

    def execute(self, command: DisableUserCommand) -> int:
        if command.actor_id == command.target_user_id:
            raise DomainError("validation_error", "You cannot disable your own account.")
        target = self._users.get_by_id(command.target_user_id)
        if target is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        target_membership = self._memberships.get_for_user(target.id)
        if target_membership is None:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        self._assert_scope(command.actor_membership, target_membership)
        self._users.update_status(target.id, UserStatus.DISABLED)
        self._memberships.update_status(target_membership.id, MembershipStatus.DISABLED)
        return self._sessions.destroy_all(target.id)

    def _assert_scope(self, actor: MembershipRecord, target: MembershipRecord) -> None:
        if actor.principal_type.value == "platform":
            # super_admin bypasses all permission checks (ADR-007).
            if actor.role == "super_admin":
                return
            # ADR-007: new code for platform user disable is user.delete
            if "user.delete" not in permissions_for_role(actor.role):
                raise DomainError("forbidden", "Not permitted.", http_status=403)
            return
        # ADR-007: new code for team disable is team.delete
        if "team.delete" not in permissions_for_role(actor.role):
            raise DomainError("forbidden", "Not permitted.", http_status=403)
        if actor.tenant_id is None or actor.tenant_id != target.tenant_id:
            raise DomainError("not_found", "Resource not found.", http_status=404)
        if actor.principal_type.value == "customer":
            if target.customer_id is None or target.customer_id != actor.customer_id:
                raise DomainError("not_found", "Resource not found.", http_status=404)
        elif target.principal_type.value == "platform":
            raise DomainError("not_found", "Resource not found.", http_status=404)
