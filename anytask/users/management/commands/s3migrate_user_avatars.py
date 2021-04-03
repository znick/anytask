# -*- coding: utf-8 -*-

from common.s3_migrate import S3MigrateCommand
from users.models import UserProfile


class Command(S3MigrateCommand):
    help = """
        Upload user avatars to S3 cloud.
        Won't delete files from local storage.
        """

    def all_models(self, options):
        return UserProfile.objects.all().exclude(avatar__name__startswith='S3/')

    def get_model_field(self, model, options):
        return model.avatar

    def update_model(self, model, new_path, options):
        try:
            model.avatar.name = new_path
            model.save()
        except Exception as e:
            print('Unhandled exception in {}: {}'.format(self.update_model, e))
            return False
        else:
            return True
