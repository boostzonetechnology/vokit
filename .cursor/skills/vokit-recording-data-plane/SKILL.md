# Vokit Recording Data Plane Skill

## Use when
Use for recording ingestion, playback/download, transcripts, artifact storage, retention, export, deletion, legal hold or recording server changes.

## Workflow
1. Resolve call/tenant/customer scope.
2. Separate metadata from raw artifact bytes.
3. Define ingestion state machine and asynchronous retry behavior.
4. Define object namespace, checksum and immutability rules.
5. Define access token/signed URL authorization.
6. Define retention, legal hold and deletion behavior.
7. Test foreign-tenant artifact access and token replay/expiry.
8. Test orphan recovery and recording-server outage.
9. Emit access, lifecycle and reconciliation telemetry.
10. Update the artifact runbook.

## Hard rule
Raw recordings never become a Django static/media file exposed through the frontend.
