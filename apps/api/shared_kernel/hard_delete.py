"""TEN-006: financial / KYC / audit rows must not be hard-deleted."""

from __future__ import annotations

from django.db import models

from shared_kernel.errors import DomainError


def assert_hard_delete_forbidden(
    *,
    code: str = "hard_delete_forbidden",
    message: str = "Financial, KYC, and audit records cannot be hard-deleted.",
) -> None:
    raise DomainError(code, message, http_status=409)


class HardDeleteForbiddenQuerySet(models.QuerySet):
    def delete(self):  # noqa: A003 — Django QuerySet API
        assert_hard_delete_forbidden()


class HardDeleteForbiddenManager(models.Manager.from_queryset(HardDeleteForbiddenQuerySet)):
    pass


class HardDeleteForbiddenModel(models.Model):
    """Abstract: instance and queryset `.delete()` raise DomainError."""

    objects = HardDeleteForbiddenManager()

    class Meta:
        abstract = True
 
    def delete(self, *args, **kwargs) -> None:  # noqa: ARG002
        assert_hard_delete_forbidden()
