# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from storage import S3OverlayStorage


def upload_to_s3(file_field, dest_storage, dry_run=True):
    """Saves content of file_field to S3, adjusting path in database

    :param file_field: django.db.models.FileField

    :param dest_storage: S3OverlayStorage

    :param dry_run: boolean, whether should only perform all checks and return
        new path without uploading

    :return: new relative path, or None if given extension is not supported by
    S3 storage

    :raise ValueError: if `dest_storage.is_s3_stored(file_field.name) == True`
    :raise KeyError: if destination path exists, with message=new_path
    """
    old_path = file_field.name
    if S3OverlayStorage.is_s3_stored(old_path):
        raise ValueError("Path with S3 magic: {}".format(old_path))
    new_path = dest_storage.append_s3_prefix(old_path)
    if dest_storage.exists(new_path):
        raise KeyError(new_path)
    if not dry_run:
        with file_field.storage.open(file_field.name, 'rb') as content:
            dest_storage.save(new_path, content)
    return new_path


class S3MigrateCommand(BaseCommand):
    """Base class for s3 migration-related commands.
    Won't delete files from local storage.
    Won't migrate files with extensions not supported by S3OverlayStorage.
    Supports only one FileField per model.

    Implementations must override all_models(), get_model_path() and
    update_model() methods.
    """

    DEST_EXISTS_NOT_OK = (
        """Error: destination already exists and --ok-if-exists not present"""
        """ (skipping db record): {}""")
    DEST_EXISTS_OK = (
        """Note: destination already exists: {}""")
    SKIP_IGNORED_EXT = "Note: skipping: ignored extension: {}"
    SKIP_ALREADY_S3 = "Note: skipping: already stored in S3 (by path): {}"
    OK_UPLOADED = "Note: uploaded: {}"
    ERR_UNHANDLED_EXCEPTION = "Error: unhandled exception: {}, {}"
    NOTE_UPDATING_MODEL = "Note: updating model: {}, {}"
    OK_UPDATED_MODEL = "Note: updated model: {}, {}"
    ERR_UPDATE_MODEL = "Error: update_model failed: {}, {}"

    def all_models(self, options):
        """
        :param options: as in BaseCommand.handle

        :return: iterator over all models to migrate
        """
        raise NotImplementedError()

    def get_model_field(self, model, options):
        """
        :param model: object obtained from iteration over all_models()

        :param options: as in BaseCommand.handle

        :return: django.db.models.FileField of model, None if should be ignored
        """
        raise NotImplementedError()

    def update_model(self, model, new_path, options):
        """Called iff upload was successful

        :param model: object obtained from iteration over all_models()

        :param new_path: path uploaded to S3 bucket, including S3 magic prefix

        :param options: as in BaseCommand.handle

        :return: True iff model updated successfully
        """
        raise NotImplementedError()

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super(S3MigrateCommand, self).__init__(stdout, stderr, no_color)
        self.rewrite_url = None
        self.rewrite_url_only_existing = None
        self.dry_run = None
        self.ignored_extensions = None
        self.dest_storage = None
        self.newly_uploaded = set()

    def add_arguments(self, parser):
        """Call super when overriding"""
        parser.add_argument(
            '--do-rewrite-url',
            dest='rewrite_url',
            action='store_true',
            default=False,
            help='Rewrite url field for files in DB, else will only upload to S3 (default: false)'
        )
        parser.add_argument(
            '--rewrite-only-existing',
            dest='rewrite_url_only_existing',
            action='store_true',
            default=False,
            help='Rewrite url field only for files already uploaded to S3 (default: false). Implies --do-rewrite-url.'
        )
        parser.add_argument(
            '--execute',
            dest='execute',
            action='store_true',
            default=False,
            help='Actually execute migration, else will only list changes (default: false)'
        )
        parser.add_argument(
            '--ignore-extension-extra',
            dest='ignore_extension',
            action='append',
            default=[],
            help='''Extra extensions to exclude from migrations (in addition '''
                 '''to unsupported). May be specified multiple times.'''
        )

    def handle(self, **options):
        self.rewrite_url_only_existing = options['rewrite_url_only_existing']
        self.rewrite_url = options['rewrite_url'] or self.rewrite_url_only_existing
        self.dry_run = not options['execute']
        self.ignored_extensions = options['ignore_extension']
        self.ignored_extensions.extend(S3OverlayStorage.IGNORED_EXTENSIONS)

        self.dest_storage = S3OverlayStorage()
        if self.dry_run:
            self.stdout.write("Note: Dry run")

        for model in self.all_models(options):
            field = self.get_model_field(model, options)
            if not field:
                continue
            old_path = field.name
            if any(map(old_path.endswith, self.ignored_extensions)):
                self.stdout.write(self.SKIP_IGNORED_EXT.format(old_path))
                continue
            if S3OverlayStorage.is_s3_stored(old_path):
                self.stdout.write(self.SKIP_ALREADY_S3.format(old_path))
                continue
            new_path = self.s3_upload(field)
            if not (new_path and self.rewrite_url):
                continue  # Upload failed or model update not required
            self.stdout.write(self.NOTE_UPDATING_MODEL.format(model, new_path))
            if self.dry_run:
                continue
            try:
                if self.update_model(model, new_path, options):
                    msg = self.OK_UPDATED_MODEL.format(model, new_path)
                else:
                    msg = self.ERR_UPDATE_MODEL.format(model, new_path)
                self.stdout.write(msg)
            except Exception as e:
                self.stdout.write(self.ERR_UNHANDLED_EXCEPTION.format(new_path, e))

    def s3_upload(self, field):
        """:return: new path if model update required, else None"""
        result = None
        try:
            new_path = upload_to_s3(field, self.dest_storage, self.dry_run)
            self.stdout.write(self.OK_UPLOADED.format(new_path))
            self.newly_uploaded.add(new_path)
            if self.rewrite_url_only_existing:
                result = None  # don't update DB model for newly uploaded files
            else:
                result = new_path
        except KeyError as e:
            new_path = e.message
            if (new_path in self.newly_uploaded) and self.rewrite_url_only_existing:
                result = None
            else:
                self.stdout.write(self.DEST_EXISTS_OK.format(new_path))
                result = new_path
        except Exception as e:
            self.stdout.write(self.ERR_UNHANDLED_EXCEPTION.format(field.name, e))
            result = None
        finally:
            return result
