from __future__ import annotations

from django.contrib.auth.hashers import check_password, make_password


class DjangoPasswordHasher:
    def hash(self, raw: str) -> str:
        return make_password(raw)

    def verify(self, raw: str, encoded: str) -> bool:
        return check_password(raw, encoded)
