# Dummy payment processor (lab)

Thin Slim host. No Stripe, Braintree, or PayPal SDKs.

Vokit remains the source of truth: invoice Paid, payment row, minute lots, and commission hold happen only after this process posts a signed webhook.

```powershell
cd packages/dummy-payment-processor
copy .env.example .env
composer install
php -S 127.0.0.1:8081 -t public
```

Health: `GET http://127.0.0.1:8081/health`

`SANDBOX_WEBHOOK_SECRET` must match `apps/api/.env`.
