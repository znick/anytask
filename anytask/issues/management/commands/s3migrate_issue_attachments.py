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
            help='Actually execute migration')
        '''
        parser.add_argument(
            '--reverse',
            dest='reverse',
            action='store_true',
            default=False,
            help='DEV ONLY')
        '''
        parser.add_argument(
            '--ignore-extensions-extra',
            dest='ignore_extensions',
            action='append',
            default=[],
            help='Don\'t migrate files with these extensions')

    def handle(self, **options):
        dry_run = not options['execute']
        ignored_extensions = options['ignore_extensions']

        if any(map(ignored_extensions.count, S3OverlayStorage.IGNORED_EXTENSIONS)):
            raise ValueError("Won't un-ignore unsupported extensions")
        if dry_run:
            print("NOTE: Dry run")
        dest_storage = S3OverlayStorage()

        for file_model in File.objects.all():
            try:
                new_path = migrate_to_s3(file_model.file, dest_storage, dry_run)
                print("Note: uploaded: {}".format(new_path))
            except KeyError as e:
                new_path = e.message
                print("Note: destination already exists: {}".format(new_path))
            except Exception as e:
                print("Unhandled exception, ignoring: {}".format(e))
                continue
            if not dry_run:
                file_model.file.name = new_path
                file_model.save()
