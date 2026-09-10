# Vokit Customer portal

Must screens (dashboard, agents, calls, usage, invoices, top-ups, risk,
notifications). Dashboard values come from `/api/v1/customer/dashboard`.
Authorization is server-side (`GET /api/v1/customer/me`). A platform or agency
user who signs in here receives **403**.

```powershell
cd h:\laragon\www\vokit
npm install
npm run dev:customer
```

A platform or agency user who signs in here receives **403**. Demo user: `customer@vokit.test` / `Phase2-Demo!ok`.
