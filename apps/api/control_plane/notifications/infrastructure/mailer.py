from __future__ import annotations

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail


class DjangoMailer:
    def send(self, *, to: str, subject: str, body: str, html_body: str = "") -> None:
        sender = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@vokit.test")
        if html_body.strip():
            message = EmailMultiAlternatives(subject, body, sender, [to])
            message.attach_alternative(html_body, "text/html")
            message.send(fail_silently=False)
            return
        send_mail(subject, body, sender, [to], fail_silently=False)
