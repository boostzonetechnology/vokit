from __future__ import annotations

from django.urls import path

from control_plane.identity.api.views import (
    AcceptInvitationView,
    CsrfView,
    DisableUserView,
    InvitationListView,
    LoginView,
    LogoutView,
    MeView,
    SessionView,
    TeamListView,
)
from control_plane.identity.domain.types import PrincipalType

urlpatterns = [
    path("auth/csrf", CsrfView.as_view(), name="auth-csrf"),
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("auth/session", SessionView.as_view(), name="auth-session"),
    path("auth/invitations/accept", AcceptInvitationView.as_view(), name="auth-invite-accept"),
    path(
        "platform/me",
        MeView.as_view(principal_type=PrincipalType.PLATFORM),
        name="platform-me",
    ),
    path(
        "platform/users",
        TeamListView.as_view(principal_type=PrincipalType.PLATFORM),
        name="platform-users",
    ),
    path(
        "platform/users/<str:user_id>/disable",
        DisableUserView.as_view(principal_type=PrincipalType.PLATFORM),
        name="platform-user-disable",
    ),
    path("platform/invitations", InvitationListView.as_view(), name="platform-invitations"),
    path(
        "agency/me",
        MeView.as_view(principal_type=PrincipalType.AGENCY),
        name="agency-me",
    ),
    path(
        "agency/team",
        TeamListView.as_view(principal_type=PrincipalType.AGENCY),
        name="agency-team",
    ),
    path(
        "agency/team/<str:user_id>/disable",
        DisableUserView.as_view(principal_type=PrincipalType.AGENCY),
        name="agency-team-disable",
    ),
    path(
        "customer/me",
        MeView.as_view(principal_type=PrincipalType.CUSTOMER),
        name="customer-me",
    ),
    path(
        "customer/team",
        TeamListView.as_view(principal_type=PrincipalType.CUSTOMER),
        name="customer-team",
    ),
    path(
        "customer/team/<str:user_id>/disable",
        DisableUserView.as_view(principal_type=PrincipalType.CUSTOMER),
        name="customer-team-disable",
    ),
]
