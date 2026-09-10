# Vokit Agency portal

Must screens (dashboard, customers, agents, numbers, calls, wallet, KYC, team).
Authorization is server-side (`GET /api/v1/agency/me`). Responsive layout
collapses navigation under 800px.

```powershell
cd h:\laragon\www\vokit
npm install
npm run dev:agency
```

A platform user who signs in here receives **403**. Demo user: `agency@vokit.test` / `Phase2-Demo!ok`.
