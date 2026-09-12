# Notifications

In-app inbox plus email (NOT-001). Templates are Super Admin managed (SA16-001).
Security, billing, KYC, and suspension notices cannot be disabled (NOT-003).
Invitation tokens are emailed and must not appear in the in-app body or delivery
log. Agency/customer preferences are scoped to the session tenant or customer.

## Email delivery (SMTP + Celery)

Outbound email is queued on Celery (broker = Redis via `REDIS_URL`):

1. `NotificationControl` renders the template and creates a delivery row with status `queued`.
2. Task `notifications.send_email` is enqueued (payload includes the rendered body; do not log it).
3. The worker calls `DjangoMailer` → Django `EmailMultiAlternatives` (HTML + plain text) and sets delivery to `sent` or `failed`.

All emails share one HTML shell (`infrastructure/email_layout.py`). Invitation CTAs use
`PLATFORM_PORTAL_PUBLIC_URL` / `AGENCY_PORTAL_PUBLIC_URL` / `CUSTOMER_PORTAL_PUBLIC_URL`
plus `/accept-invite?token=…`.

### Env (see `apps/api/.env.example`)

- `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD_REF` / `EMAIL_HOST_PASSWORD` (secret ref; never commit real passwords)
- `EMAIL_USE_TLS` / `EMAIL_USE_SSL`, `DEFAULT_FROM_EMAIL`
- `PLATFORM_PORTAL_PUBLIC_URL`, `AGENCY_PORTAL_PUBLIC_URL`, `CUSTOMER_PORTAL_PUBLIC_URL`
- `REDIS_URL`, `CELERY_TASK_ALWAYS_EAGER`

### Local

- Default local settings use `CELERY_TASK_ALWAYS_EAGER=true`: the Celery task runs **inline** in the API process (still the same task code; Redis consumer not required).
- For a real queue: start Redis, set `CELERY_TASK_ALWAYS_EAGER=0`, run:

```powershell
cd apps/api
.\.venv\Scripts\celery.exe -A config.celery worker -l info
```

Then create an agency/customer invite and confirm SMTP delivery + delivery log status.
