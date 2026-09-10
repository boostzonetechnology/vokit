from __future__ import annotations

from control_plane.identity.application.ports import SessionGateway


class LogoutUser:
    def __init__(self, sessions: SessionGateway) -> None:
        self._sessions = sessions

    def execute(self) -> None:
        self._sessions.destroy_current()
