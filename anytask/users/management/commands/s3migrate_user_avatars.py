# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from storage import S3OverlayStorage, migrate_to_s3
from users.models import UserProfile


class Command(BaseCommand):
    help = """Upload user avatars to S3 cloud.
    Won't delete files from local storage.
    """

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

    def handle(self, **options):
        dry_run = not options['execute']

        if dry_run:
            print("NOTE: Dry run")
        dest_storage = S3OverlayStorage()

        for user_model in UserProfile.objects.all():
            if not user_model.avatar:
                continue
            try:
                new_path = migrate_to_s3(user_model.avatar, dest_storage, dry_run)
                print("Note: uploaded: {}".format(new_path))
            except KeyError as e:
                new_path = e.message
                print("Note: destination already exists: {}".format(new_path))
            except Exception as e:
                print("Unhandled exception, ignoring: {}".format(e))
                continue
            if not dry_run:
                user_model.avatar.name = new_path
                user_model.save()
