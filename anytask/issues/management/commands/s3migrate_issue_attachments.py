# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage

from storage import S3OverlayStorage
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
        parser.add_argument(
            '--reverse',
            dest='reverse',
            action='store_true',
            default=False,
            help='DEV ONLY')
        parser.add_argument(
            '--ignore-extensions-extra',
            dest='ignore_extensions',
            action='append',
            default=[],
            help='Don\'t migrate files with these extensions')

    def handle(self, **options):
        dry_run = not options['execute']
        ignored_extensions = options['ignore_extensions']
        reverse = options['reverse']

        if any(map(ignored_extensions.count, S3OverlayStorage.IGNORED_EXTENSIONS)):
            print("Won't un-ignore unsupported extensions")
        if dry_run:
            print("NOTE: Dry run")
        
        for file_model in File.objects.all():
            self.migrate_file(file_model, dry_run, reverse)

    @staticmethod
    def migrate_file(model, dry_run, reverse):
        file_field = model.file
        is_s3 = S3OverlayStorage.is_s3_stored(file_field.name)
        if reverse != is_s3:
            return
        if reverse:
            new_name = file_field.name.replace('S3/media//', '')
        else:
            new_name = S3OverlayStorage.append_s3_prefix(file_field.name)
        print("{} -> {}".format(file_field.name, new_name))
        if not dry_run:
            with file_field.storage.open(file_field.name, 'rb') as content:
                default_storage.save(new_name, content)
            file_field.name = new_name
            model.save()
