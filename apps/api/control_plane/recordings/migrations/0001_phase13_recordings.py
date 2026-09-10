import shared_kernel.ids
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="RecordingArtifactIndex",
            fields=[
                ("id", models.UUIDField(primary_key=True, serialize=False)),
                ("tenant_id", models.UUIDField()),
                ("customer_id", models.UUIDField()),
                ("call_id", models.UUIDField()),
                ("kind", models.CharField(max_length=32)),
                ("object_key", models.CharField(max_length=255)),
                ("checksum", models.CharField(max_length=80)),
                ("status", models.CharField(max_length=16)),
                ("legal_hold", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"db_table": "recording_artifact_index"},
        ),
        migrations.CreateModel(
            name="RecordingIngestEvent",
            fields=[
                ("event_id", models.CharField(max_length=128, primary_key=True, serialize=False)),
                ("artifact_id", models.UUIDField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "recording_ingest_events"},
        ),
        migrations.CreateModel(
            name="RecordingAccessGrant",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=shared_kernel.ids.new_uuid7,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("token_hash", models.CharField(max_length=64, unique=True)),
                ("artifact_id", models.UUIDField()),
                ("tenant_id", models.UUIDField()),
                ("customer_id", models.UUIDField()),
                ("call_id", models.UUIDField()),
                ("actor_id", models.UUIDField()),
                ("status", models.CharField(default="issued", max_length=16)),
                ("expires_at", models.DateTimeField()),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "recording_access_grants"},
        ),
        migrations.AddIndex(
            model_name="recordingartifactindex",
            index=models.Index(fields=["tenant_id", "call_id"], name="idx_rec_idx_call"),
        ),
        migrations.AddIndex(
            model_name="recordingartifactindex",
            index=models.Index(fields=["object_key"], name="idx_rec_idx_object"),
        ),
        migrations.AddIndex(
            model_name="recordingaccessgrant",
            index=models.Index(
                fields=["artifact_id", "status"], name="idx_rec_grant_artifact"
            ),
        ),
    ]
