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


# ---------------------------------------------------------------------------
# RBAC — ADR-007
# ---------------------------------------------------------------------------


class Permission(models.Model):
    """A fine-grained capability. Codes: {module}.{action}, e.g. agent.view."""

    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    namespace = models.CharField(max_length=32)  # platform | agency | customer
    code = models.CharField(max_length=64)
    description = models.CharField(max_length=255, blank=True)
    is_sensitive = models.BooleanField(default=False)
    is_custom = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_permissions"
        unique_together = [("namespace", "code")]

    def __str__(self) -> str:
        return f"{self.namespace}:{self.code}"


class Role(models.Model):
    """A named permission bundle. Slug is unique across all namespaces."""

    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    namespace = models.CharField(max_length=32)  # platform | agency | customer
    slug = models.CharField(max_length=64, unique=True)
    display_name = models.CharField(max_length=128)
    is_system = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_roles"

    def __str__(self) -> str:
        return self.slug


class RolePermission(models.Model):
    """Pivot: role → permission. super_admin has no rows (bypass)."""

    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="role_permissions")
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name="role_permissions"
    )

    class Meta:
        db_table = "identity_role_permissions"
        unique_together = [("role", "permission")]


# ---------------------------------------------------------------------------
# Membership & Invitation (updated for ADR-007)
# ---------------------------------------------------------------------------


class Membership(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="membership")
    principal_type = models.CharField(max_length=16)
    # role CharField removed; replaced by FK (DB column: role_id).
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memberships",
    )
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
    # role CharField removed; replaced by FK (DB column: role_id).
    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitations",
    )
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


# ---------------------------------------------------------------------------
# MFA (SEC-013 / RBAC-008) — TOTP + Email OTP
# ---------------------------------------------------------------------------


class MfaMethod(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mfa_methods")
    method_type = models.CharField(max_length=16)  # totp | email
    status = models.CharField(max_length=16, default="pending")  # pending|active|disabled
    secret_ciphertext = models.CharField(max_length=1024, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    disabled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "identity_mfa_methods"
        indexes = [
            models.Index(fields=["user", "status"], name="idx_mfa_method_user"),
        ]


class MfaChallenge(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mfa_challenges")
    purpose = models.CharField(max_length=16)  # login | enroll | disable
    method = models.ForeignKey(
        MfaMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="challenges",
    )
    token_hash = models.CharField(max_length=64, unique=True)
    code_hash = models.CharField(max_length=64, blank=True, default="")
    expires_at = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=5)
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_mfa_challenges"
        indexes = [
            models.Index(fields=["user", "purpose"], name="idx_mfa_chal_user"),
        ]


class MfaRecoveryCode(models.Model):
    id = models.UUIDField(primary_key=True, default=new_uuid7, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mfa_recovery_codes")
    code_hash = models.CharField(max_length=64)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "identity_mfa_recovery_codes"
        indexes = [
            models.Index(fields=["user", "used_at"], name="idx_mfa_recovery_user"),
        ]
