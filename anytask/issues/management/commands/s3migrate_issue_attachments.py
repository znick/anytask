# -*- coding: utf-8 -*-

from storage import S3OverlayStorage
from common.s3_migrate import S3MigrateCommand
from issues.models import File


class Command(S3MigrateCommand):
    help = """
        Upload issue attachments to S3 cloud.
        Won't delete files from local storage.
        Won't migrate files with following extensions:
        {}
        """.format(', '.join(S3OverlayStorage.IGNORED_EXTENSIONS))

    def all_models(self, options):
        return File.objects.all().exclude(file__startswith='S3/')

    def get_model_field(self, model, options):
        return model.file

    def update_model(self, model, new_path, options):
        try:
            model.file.name = new_path
            model.save()
        except Exception as e:
            print('Unhandled exception in {}: {}'.format(self.update_model, e))
            return False
        else:
            return True
