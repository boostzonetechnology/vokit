from __future__ import annotations

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.db import models
from django.db.models import Q

from shared_kernel.ids import new_uuid7


class UserManager(BaseUserManager["User"]):
    def create_user(self, email: str, password: str | None = None, **extra: object) -> User:
        if not email:
            raise ValueError("email is required")
        user = self.model(email=str(email).strip().lower(), **extra)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    email = models.EmailField(unique=True)
    status = models.CharField(max_length=16, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        db_table = "identity_users"

    @property
    def is_staff(self) -> bool:
        return False

    @property
    def is_active(self) -> bool:
        return self.status == "active"


class Membership(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="membership")
    principal_type = models.CharField(max_length=16)
    role = models.CharField(max_length=64)
    tenant_id = models.UUIDField(null=True, blank=True)
    customer_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(max_length=16, default="active")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_memberships"
        constraints = [
            models.CheckConstraint(
                name="identity_membership_scope",
                condition=(
                    (
                        Q(principal_type="platform")
                        & Q(tenant_id__isnull=True)
                        & Q(customer_id__isnull=True)
                    )
                    | (
                        Q(principal_type="agency")
                        & Q(tenant_id__isnull=False)
                        & Q(customer_id__isnull=True)
                    )
                    | (
                        Q(principal_type="customer")
                        & Q(tenant_id__isnull=False)
                        & Q(customer_id__isnull=False)
                    )
                ),
            ),
        ]


class Invitation(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    email = models.EmailField()
    principal_type = models.CharField(max_length=16)
    role = models.CharField(max_length=64)
    tenant_id = models.UUIDField(null=True, blank=True)
    customer_id = models.UUIDField(null=True, blank=True)
    token_hash = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=16, default="invited")
    expires_at = models.DateTimeField()
    invited_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name="sent_invitations"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_invitations"


class UserSession(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    session_key = models.CharField(max_length=40, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_user_sessions"
