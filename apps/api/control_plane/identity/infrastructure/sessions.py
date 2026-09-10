from __future__ import annotations

import uuid

from django.contrib.auth import login, logout
from django.contrib.sessions.models import Session
from django.http import HttpRequest

from control_plane.identity.models import User, UserSession


class DjangoSessionGateway:
    def __init__(self, request: HttpRequest) -> None:
        self._request = request

    def create(self, user_id: uuid.UUID) -> str:
        user = User.objects.get(pk=user_id)
        previous_key = self._request.session.session_key
        login(self._request, user, backend="django.contrib.auth.backends.ModelBackend")
        if not self._request.session.session_key:
            self._request.session.save()
        self._request.session.modified = True
        session_key = self._request.session.session_key
        if not session_key:
            raise RuntimeError("session_key missing after login")
        if previous_key and previous_key != session_key:
            UserSession.objects.filter(session_key=previous_key).delete()
        UserSession.objects.get_or_create(user=user, session_key=session_key)
        return session_key

    def destroy_current(self) -> None:
        key = self._request.session.session_key
        logout(self._request)
        if key:
            UserSession.objects.filter(session_key=key).delete()

    def destroy_all(self, user_id: uuid.UUID) -> int:
        rows = list(UserSession.objects.filter(user_id=user_id))
        keys = [row.session_key for row in rows]
        if keys:
            Session.objects.filter(session_key__in=keys).delete()
        deleted, _ = UserSession.objects.filter(user_id=user_id).delete()
        return deleted
