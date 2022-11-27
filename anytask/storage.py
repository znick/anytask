import os.path
from django.core.files.storage import FileSystemStorage, Storage
from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


class S3OverlayStorage(Storage):
    """Delegate paths starting with S3 magic to S3 storage
    Delegate other paths to local storage
    No extra fields required in models
    See `_dispatch` method

    Some file types (ipynb, archives) currently must be stored locally
    See `_is_local_only` method
    """

    S3_STORED_MAGIC = 'S3'
    S3_STORED_PREFIX = S3_STORED_MAGIC + settings.MEDIA_URL
    _S3_SKIP_LEN = len(S3_STORED_MAGIC + '/')
    _MEDIA_SKIP_LEN = len(settings.MEDIA_URL + '/')

    IGNORED_EXTENSIONS = []

    def __init__(self, *args, **kwargs):
        self.local_storage = FileSystemStorage(*args, **kwargs)
        self.s3_storage = S3Boto3Storage(*args, **kwargs)

    @classmethod
    def _is_local_only(cls, name):
        return any(map(name.endswith, cls.IGNORED_EXTENSIONS))

    def _adjust_path(self, name, storage):
        """S3Boto3Storage ignores ("expected behaviour") MEDIA_URL from settings, so we
        add it to S3_STORAGE_PREFIX manually
        TODO leave a link to issue

        /<S3_STORED_MAGIC>/rel_path -> /<S3_STORED_MAGIC>/<MEDIA_URL>/rel_path
        """
        if storage is self.local_storage:
            return name
        if not name.startswith(self.S3_STORED_PREFIX):
            raise ValueError("S3 path not starting with S3 prefix")
        return os.path.join([
            self.S3_STORED_MAGIC, settings.MEDIA_URL, name[self._S3_SKIP_LEN:]
        ])

    def _dispatch(self, name, method_name, *args, **kwargs):
        if self.s3_storage is None:
            storage = self.local_storage
        elif self._is_local_only(name):
            storage = self.local_storage
        elif self.is_s3_stored(name):
            storage = self.s3_storage
        else:
            storage = self.local_storage
        method = getattr(storage, method_name)
        return method(name, *args, **kwargs)

    @classmethod
    def is_s3_stored(cls, name):
        return name.lstrip('/').startswith(cls.S3_STORED_MAGIC + '/')

    @classmethod
    def append_s3_prefix(cls, relative_path):
        """Adjust relative path so that it maps to S3

        :raise ValueError - if path already starts with S3 prefix
        """
        if relative_path.startswith(cls.S3_STORED_MAGIC):
            raise ValueError("Path already starts with S3 magic, must be relative")
        return '/'.join([cls.S3_STORED_PREFIX, relative_path])

    def accessed_time(self, name):
        return self._dispatch(name, 'accessed_time')

    def created_time(self, name):
        return self._dispatch(name, 'created_time')

    def delete(self, name):
        return self._dispatch(name, 'delete')

    def exists(self, name):
        return self._dispatch(name, 'exists')

    def get_accessed_time(self, name):
        return self._dispatch(name, 'get_accessed_time')

    def get_available_name(self, name, max_length=None):
        return self._dispatch(name, 'get_available_name',
                              max_length=max_length)

    def get_created_time(self, name):
        return self._dispatch(name, 'get_created_time')

    def get_modified_time(self, name):
        return self._dispatch(name, 'get_modified_time')

    def get_valid_name(self, name):
        return self._dispatch(name, 'get_valid_name')

    def generate_filename(self, filename):
        return self._dispatch(filename, 'generate_filename')

    def listdir(self, path):
        return self._dispatch(path, 'listdir')

    def modified_time(self, name):
        return self._dispatch(name, 'modified_time')

    def open(self, name, mode='rb'):
        return self._dispatch(name, 'open',
                              mode=mode)

    def path(self, name):
        """May fail when called with S3 path: S3Boto3Storage doesn't implement this
        method
        """
        return self._dispatch(name, 'path')

    def save(self, name, content, max_length=None):
        return self._dispatch(name, 'save',
                              content=content, max_length=max_length)

    def size(self, name):
        return self._dispatch(name, 'size')

    def url(self, name):
        return self._dispatch(name, 'url')


class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        """Returns a filename that's free on the target storage system, and
        available for new content to be written to.

        Found at http://djangosnippets.org/snippets/976/

        This file storage solves overwrite on upload problem. Another
        proposed solution was to override the save method on the model
        like so (from https://code.djangoproject.com/ticket/11663):

        def save(self, *args, **kwargs):
            try:
                this = MyModelName.objects.get(id=self.id)
                if this.MyImageFieldName != self.MyImageFieldName:
                    this.MyImageFieldName.delete()
            except: pass
            super(MyModelName, self).save(*args, **kwargs)
        """
        # If the filename already exists, remove it as if it was a true file system
        if self.exists(name):
            self.delete(name)
        # FIXME
        if (max_length is not None) and (len(name) > max_length):
            return name[:max_length]
        else:
            return name
