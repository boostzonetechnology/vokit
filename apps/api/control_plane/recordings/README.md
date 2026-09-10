# Recording metadata

Django stores artifact metadata and issues short-lived single-use access grants.
Raw audio never lands in `MEDIA`/`static` and is never streamed by this app.

Object namespace: `tenant/{tenant_id}/calls/{call_id}/artifacts/{artifact_id}`.

Ingest (`POST /internal/recordings/v1/ingest/`) authenticates with
`VOKIT_INTERNAL_RECORDING_TOKEN`. Tenant routing comes from `call_index`, not the body.

Playback: authorize call + artifact, then `POST .../artifacts/{id}/access` returns
`{token, expires_at, url}` pointing at the recording plane. The plane must call
`POST /internal/recordings/v1/access/validate/`. Expired and replayed tokens fail.

Retention and legal hold live on tenant artifact rows. Delete is a status change after
the retention window and only when hold is off. `reconcile_recordings` reports
orphan objects and orphan metadata.

Call completion must not wait on ingest. A recording-store outage leaves artifacts
`verifying` and does not rewrite call rows.
