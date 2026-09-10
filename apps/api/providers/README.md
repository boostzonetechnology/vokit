# Provider adapters

Domain code must not import vendor SDKs. Adapters land when their phase starts (billing, KYC, telephony).

KYC hosted-session adapter: `providers/kyc/hosted.py`.  
Payment adapters: `providers/billing/stripe.py` and `providers/billing/braintree.py`. Vendor SDKs stay out of the domain.

Number inventory adapter: `providers/telephony/memory.py`. Empty/local environments do not call a carrier SDK.
