from django.core.files.storage import FileSystemStorage, Storage
from storages.backends.s3boto3 import S3Boto3Storage


class S3OverlayStorage(Storage):
    """
    Delegate paths starting with S3 magic to S3 storage
    Delegate other paths to local storage
    No extra fields required in models
    See `_dispatch` method
    """

    S3_STORED_MAGIC = 'S3_STORED_MAGIC'

    def __init__(self, *args, **kwargs):
        self.local_storage = FileSystemStorage(*args, **kwargs)
        self.s3_storage = S3Boto3Storage(*args, **kwargs)

    def _dispatch(self, name, method_name, *args, **kwargs):
        if name.lstrip('/').startswith(self.S3_STORED_MAGIC) and self.s3_storage:
            method = getattr(self.s3_storage, method_name)
        else:
            method = getattr(self.local_storage, method_name)
        return method(name, *args, **kwargs)

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
        return self._dispatch(name, 'path')

    def save(self, name, content, max_length=None):
        return self._dispatch(name, 'save',
                              content=content, max_length=max_length)

    def size(self, name):
        return self._dispatch(name, 'size')

    def url(self, name):
        return self._dispatch(name, 'url')


class OverwriteStorage(S3OverlayStorage):
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
