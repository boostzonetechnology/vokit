# Key rotation

Rotate by changing the **secret ref value** in the secret manager, then dual-accept old+new only if the adapter supports it. Do not put new keys in git or React.

In scope: Stripe/Braintree webhook secrets, KYC webhook secret, telephony internal token, recording token HMAC, tenant DB passwords (per tenant), session `DJANGO_SECRET_KEY` (session invalidation expected).

After rotation: replay a signed sandbox webhook, one internal telephony bootstrap, one recording access grant.
