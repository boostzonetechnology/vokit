from __future__ import annotations

from urllib.parse import quote

from django.conf import settings

from control_plane.identity.domain.types import PrincipalType


def portal_public_url(principal_type: PrincipalType) -> str:
    if principal_type is PrincipalType.AGENCY:
        return str(getattr(settings, "AGENCY_PORTAL_PUBLIC_URL", "") or "").rstrip("/")
    if principal_type is PrincipalType.CUSTOMER:
        return str(getattr(settings, "CUSTOMER_PORTAL_PUBLIC_URL", "") or "").rstrip("/")
    return str(getattr(settings, "PLATFORM_PORTAL_PUBLIC_URL", "") or "").rstrip("/")


def invitation_accept_url(*, principal_type: PrincipalType, token: str) -> str:
    base = portal_public_url(principal_type)
    if not base:
        if principal_type is PrincipalType.PLATFORM:
            base = "http://localhost:5173"
        elif principal_type is PrincipalType.CUSTOMER:
            base = "http://localhost:5175"
        else:
            base = "http://localhost:5174"
    return f"{base}/accept-invite?token={quote(token, safe='')}"
