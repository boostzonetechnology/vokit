from __future__ import annotations

from datetime import timedelta

from django.http import HttpRequest

from control_plane.identity.application.accept_invitation import AcceptInvitation
from control_plane.identity.application.authenticate import AuthenticateUser
from control_plane.identity.application.disable_user import DisableUser
from control_plane.identity.application.invite_user import InviteUser
from control_plane.identity.infrastructure.clock import SystemClock
from control_plane.identity.infrastructure.passwords import DjangoPasswordHasher
from control_plane.identity.infrastructure.rate_limit import CacheLoginRateLimiter
from control_plane.identity.infrastructure.repositories import (
    DjangoInvitationRepository,
    DjangoMembershipRepository,
    DjangoUserRepository,
)
from control_plane.identity.infrastructure.sessions import DjangoSessionGateway

INVITE_TTL = timedelta(days=7)


def users() -> DjangoUserRepository:
    return DjangoUserRepository()


def memberships() -> DjangoMembershipRepository:
    return DjangoMembershipRepository()


def invitations() -> DjangoInvitationRepository:
    return DjangoInvitationRepository()


def invite_user() -> InviteUser:
    return InviteUser(users(), memberships(), invitations(), SystemClock(), INVITE_TTL)


def accept_invitation() -> AcceptInvitation:
    from control_plane.customers.application.change_customer import (
        ActivateCustomerOnInviteAccept,
    )
    from control_plane.customers.infrastructure.repositories import (
        DjangoCustomerIndexRepository,
    )
    from control_plane.tenancy.infrastructure.container import lifecycle

    return AcceptInvitation(
        users(),
        memberships(),
        invitations(),
        DjangoPasswordHasher(),
        SystemClock(),
        ActivateCustomerOnInviteAccept(
            DjangoCustomerIndexRepository(),
            lifecycle(),
            SystemClock(),
        ),
    )


def authenticate_user(request: HttpRequest) -> AuthenticateUser:
    return AuthenticateUser(
        users(),
        memberships(),
        DjangoPasswordHasher(),
        DjangoSessionGateway(request),
        CacheLoginRateLimiter(),
    )


def disable_user(request: HttpRequest) -> DisableUser:
    return DisableUser(users(), memberships(), DjangoSessionGateway(request))


def session_gateway(request: HttpRequest) -> DjangoSessionGateway:
    return DjangoSessionGateway(request)
