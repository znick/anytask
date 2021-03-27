# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from storage import S3OverlayStorage, migrate_to_s3
from issues.models import File


class Command(BaseCommand):
    help = """Upload issue attachments to S3 cloud.
    Won't delete files from local storage.
    Won't migrate files with following extensions:
    {}
    """.format(', '.join(S3OverlayStorage.IGNORED_EXTENSIONS))

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            dest='execute',
            action='store_true',
            default=False,
            help='Actually execute migration, else dry run')
        parser.add_argument(
            '--ok-if-exists',
            dest='ok_if_exists',
            action='store_true',
            default=False,
            help='''If set and destination already exists in S3, just update '''
                 '''db record. If not set, report error on file. It\'s normal, '''
                 '''as many File records may reference same path. '''
                 '''Sensible to set to true. Default is false.'''
        )
        parser.add_argument(
            '--ignore-extension-extra',
            dest='ignore_extension',
            action='append',
            default=[],
            help='''Extra extensions to exclude from migrations (in addition '''
                 '''to unsupported)''')

    def handle(self, **options):
        dry_run = not options['execute']
        ok_if_exists = options['ok_if_exists']
        ignored_extensions = options['ignore_extension']
        ignored_extensions.extend(S3OverlayStorage.IGNORED_EXTENSIONS)

        dest_storage = S3OverlayStorage()
        if dry_run:
            print("NOTE: Dry run")

        for file_model in File.objects.all():
            old_path = file_model.file.name
            if any(map(old_path.endswith, ignored_extensions)):
                print("Note: skipping: ignored extension: {}".format(old_path))
                continue
            if S3OverlayStorage.is_s3_stored(old_path):
                print("Note: skipping: already stored in S3: {}".format(old_path))
                continue
            try:
                new_path = migrate_to_s3(file_model.file, dest_storage, dry_run)
                print("Note: uploaded: {}".format(new_path))
            except KeyError as e:
                new_path = e.message
                if ok_if_exists:
                    print("Warning: destination already exists (will update db record): {}"
                          .format(new_path))
                else:
                    print("Error: destination already exists and --ok-if-exists not present (skipping db record): {}"
                          .format(new_path))
                    continue
            except Exception as e:
                print("Error: migrate failed: unhandled exception: {}, {}".format(old_path, e))
                continue
            if not dry_run:
                file_model.file.name = new_path
                file_model.save()
