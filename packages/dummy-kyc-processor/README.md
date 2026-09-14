# Dummy KYC processor (lab)

Thin Slim host. Agency uploads stay on this server. Vokit never stores KYC document bytes (ADR-005).

Mark **verified** or **rejected** here. Vokit updates KYC status from the signed webhook. Super Admin still activates the agency.

```powershell
cd packages/dummy-kyc-processor
copy .env.example .env
composer install
php -S 127.0.0.1:8082 -t public
```

Health: `GET http://127.0.0.1:8082/health`

`KYC_WEBHOOK_SECRET` must match `apps/api/.env`. Point Django `KYC_HOSTED_BASE_URL` at `http://127.0.0.1:8082` (HTTP allowed in local settings).
