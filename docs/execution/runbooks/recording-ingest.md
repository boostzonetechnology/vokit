# Recording ingest

1. Call completion must not wait on portal upload.
2. Ingest: available → fetch → checksum → metadata ready. Retry failures.
3. Expired or replayed access tokens fail. Artifact ID alone is insufficient.
4. Outage must not corrupt call metadata. Run `reconcile_recordings` for orphan objects/metadata.
5. Legal hold blocks deletion. Do not `DELETE` call rows to hide a backlog.

Evidence: `test_recording_negative_matrix`, `test_recording_outage_does_not_corrupt_call_and_orphans_are_visible`.
