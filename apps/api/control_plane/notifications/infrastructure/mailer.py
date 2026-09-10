from __future__ import annotations

from django.conf import settings
from django.core.mail import send_mail


class DjangoMailer:
    def send(self, *, to: str, subject: str, body: str) -> None:
        sender = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@vokit.test")
        send_mail(subject, body, sender, [to], fail_silently=False)
