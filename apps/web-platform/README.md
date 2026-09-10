# Vokit Platform portal

Must screens (dashboard, agencies, customers, KYC, agents, numbers, finance,
audit, settings). Authorization is server-side (`GET /api/v1/platform/me`).
Dashboard values come from `/api/v1/platform/dashboard`, not client math.
Period presets include today / 7d / 30d / mtd / custom with an explicit timezone.
Core flows use landmarks, labeled fields, skip-to-content, and visible focus.

```powershell
cd h:\laragon\www\vokit
npm install
npm run dev:platform
```

Proxies `/api` to `http://127.0.0.1:8000`. Demo user after `python manage.py seed_phase2_demo`: `platform@vokit.test` / `Phase2-Demo!ok`.
