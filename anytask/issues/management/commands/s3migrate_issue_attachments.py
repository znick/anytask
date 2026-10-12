# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from django.utils import timezone

from common.s3_migrate import S3NotFound, upload_to_s3
from common.s3_rollout import ready_to_delete_local
from issues.models import File
from storage import S3OverlayStorage


class Command(BaseCommand):
    help = """
        Phase 1 (always runs): upload every File not yet uploaded to S3
        (s3_uploaded_at IS NULL). Does NOT touch file.name; anytask keeps
        serving the local copy for these until T1 (see common/s3_rollout.py).

        Phase 2 (only with --delete-local-copies): for files already
        uploaded whose effective T2 threshold has passed, flip file.name to
        the S3 path and delete the local copy.

        Won't migrate files with following extensions:
        {}
        """.format(', '.join(S3OverlayStorage.IGNORED_EXTENSIONS))

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            dest='execute',
            action='store_true',
            default=False,
            help='Actually upload bytes / flip+delete, else dry-run only (default: false)'
        )
        parser.add_argument(
            '--delete-local-copies',
            dest='delete_local_copies',
            action='store_true',
            default=False,
            help='Also run phase 2 for files past their effective T2 (default: false)'
        )
        parser.add_argument(
            '--ignore-extension-extra',
            dest='ignore_extension',
            action='append',
            default=[],
            help='''Extra extensions to exclude from phase 1 upload (in addition '''
                 '''to unsupported). May be specified multiple times.'''
        )

    def handle(self, **options):
        self.execute = options['execute']
        self.delete_local_copies = options['delete_local_copies']
        self.ignored_extensions = list(options['ignore_extension']) + list(S3OverlayStorage.IGNORED_EXTENSIONS)
        self.dest_storage = S3OverlayStorage()

        if not self.execute:
            self.stdout.write("Note: Dry run")

        self._phase1_upload()

        if self.delete_local_copies:
            self._phase2_flip_and_delete()

    def _phase1_upload(self):
        for model in File.objects.filter(s3_uploaded_at__isnull=True):
            old_path = model.file.name
            if not old_path:
                continue
            if any(map(old_path.endswith, self.ignored_extensions)):
                self.stdout.write("Note: skipping: ignored extension: {}".format(old_path))
                continue
            if S3OverlayStorage.is_s3_stored(old_path):
                # Defensive only; shouldn't happen given the filter above.
                continue

            try:
                new_path = upload_to_s3(model.file, self.dest_storage, dry_run=not self.execute)
                self.stdout.write("Note: uploaded: {}".format(new_path))
            except S3NotFound as e:
                self.stdout.write("Note: destination already exists: {}".format(e.name))
            except Exception as e:
                self.stdout.write("Error: unhandled exception: {}, {}".format(old_path, e))
                continue

            if not self.execute:
                continue
            model.s3_uploaded_at = timezone.now()
            try:
                model.save(update_fields=['s3_uploaded_at'])
            except Exception as e:
                self.stdout.write("Error: update_model failed: {}, {}".format(model, e))

    def _phase2_flip_and_delete(self):
        candidates = File.objects.filter(s3_uploaded_at__isnull=False).exclude(file__startswith='S3/')
        for model in candidates:
            if not ready_to_delete_local(model.s3_uploaded_at):
                continue
            old_path = model.file.name
            new_path = self.dest_storage.append_s3_prefix(old_path)
            if not self.execute:
                self.stdout.write("Note: would flip + delete local: {} -> {}".format(old_path, new_path))
                continue
            try:
                model.file.name = new_path
                model.save(update_fields=['file'])
                self.stdout.write("Note: updated model: {}, {}".format(model, new_path))
            except Exception as e:
                self.stdout.write("Error: update_model failed: {}, {}".format(model, e))
                continue
            try:
                self.dest_storage.delete(old_path)
                self.stdout.write("Note: deleted local: {}".format(old_path))
            except Exception as e:
                self.stdout.write("Error: delete local: {}: {}".format(old_path, e))
