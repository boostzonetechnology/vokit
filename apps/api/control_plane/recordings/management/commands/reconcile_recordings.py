from __future__ import annotations

from django.core.management.base import BaseCommand

from control_plane.recordings.infrastructure.container import recording_control


class Command(BaseCommand):
    help = "Detect orphan recording objects and orphan artifact metadata."

    def handle(self, *args, **options) -> None:
        report = recording_control().reconcile()
        objects = report["orphan_objects"]
        metadata = report["orphan_metadata"]
        self.stdout.write(
            f"orphan_objects={len(objects)} orphan_metadata={len(metadata)}"
        )
        for key in objects:
            self.stdout.write(f"orphan_object {key}")
        for artifact_id in metadata:
            self.stdout.write(f"orphan_metadata {artifact_id}")
