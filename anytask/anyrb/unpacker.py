import os
import subprocess
import tempfile
import shutil
import logging

from django.conf import settings

from contextlib import contextmanager

DEVNULL = open(os.devnull, "w")

TAR = ["tar", "xf"]
_7Z = ["7z", "x"]
ARCHIVERS = {
    '.tar.gz': TAR,
    '.tar.bz2': TAR,
    '.tgz': TAR,
    '.tbz': TAR,
    '.tar.xz': TAR,
    '.zip': _7Z,
    '.rar': _7Z,
    '.7z': _7Z,
}

logger = logging.getLogger('django.request')


class UnpackedFile(object):
    def __init__(self, path, filename):
        self.path = path
        self.file = open(path)
        self._filename = filename

    def filename(self):
        return self._filename

    def __del__(self):
        self.file.close()


def get_archiver(filename):
    for suffix, archiver in ARCHIVERS.iteritems():
        if filename.lower().endswith(suffix):
            return archiver
    return None


@contextmanager
def unpack_files(files):
    res = []
    tmp_dirs = []
    for f in files:
        archiver = get_archiver(f.filename())
        if not archiver:
            res.append(f)
            continue

        dst_dir = tempfile.mkdtemp(prefix="anytask_unpack_")
        tmp_dirs.append(dst_dir)
        cmd = archiver + [os.path.join(settings.MEDIA_ROOT, f.file.name)]
        subprocess.check_call(cmd, cwd=dst_dir, stdout=DEVNULL, stderr=DEVNULL)

        for root, dirs, files in os.walk(dst_dir):
            for unpacked_file in files:
                try:
                    unpacked_filepath = os.path.join(root, unpacked_file)
                    unpacked_filename = unpacked_filepath[len(dst_dir):]
                    unpacked_filename = unpacked_filename.decode("utf-8", errors="ignore")
                    unpacked_file = UnpackedFile(unpacked_filepath, f.filename() + unpacked_filename)
                    res.append(unpacked_file)
                except Exception as e:
                    logger.exception("Exception while making UnpackedFile object for archive file '%s' in '%s', '%s'",
                                     unpacked_file, root, e)

    yield res

    for tmp_dir in tmp_dirs:
        shutil.rmtree(tmp_dir)
