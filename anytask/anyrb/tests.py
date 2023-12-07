import os

from django.test import TestCase
from .unpacker import UnpackedFile, unpack_files

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DIR = os.path.join(CUR_DIR, "test_data")


class UnpackerTest(TestCase):
    def test_no_change_on_no_archive(self):
        files = [
            UnpackedFile(os.path.join(TEST_DIR, "1.txt"), u"1.txt"),
            UnpackedFile(os.path.join(TEST_DIR, "1.py"), u"1.py"),
            UnpackedFile(os.path.join(TEST_DIR, "1.py"), u"1.py"),
            UnpackedFile(os.path.join(TEST_DIR, "1.pl"), u"1.pl"),
            UnpackedFile(os.path.join(TEST_DIR, "test.cpp"), u"test.cpp"),
            UnpackedFile(os.path.join(TEST_DIR, "test.c"), u"test.c"),
        ]

        with unpack_files(files) as unpacked_files:
            self.assertListEqual(files, unpacked_files)

    def _test_unpack(self, arcfilename):
        files = [
            UnpackedFile(os.path.join(TEST_DIR, "1.txt"), u"1.txt"),
            UnpackedFile(os.path.join(TEST_DIR, arcfilename), arcfilename),
        ]

        with unpack_files(files) as unpacked_files:
            unpacked_filenames = list(map(lambda x: x.filename(), unpacked_files))
            self.assertListEqual(['1.txt', arcfilename + '/1.py', arcfilename + '/dir/1.pl'], unpacked_filenames)

    def test_unpack_zip(self):
        self._test_unpack("zipfile.zip")

    def test_unpack_7z(self):
        self._test_unpack("7zfile.7z")

    def test_unpack_rar(self):
        self._test_unpack("rarfile.rar")

    def test_upack_tar_bz(self):
        self._test_unpack("tarfile.tar.bz2")
        self._test_unpack("tarfile.tbz")

    def test_upack_tar_gz(self):
        self._test_unpack("tarfile.tar.gz")
        self._test_unpack("tarfile.tgz")

    def test_unpack_tar_xz(self):
        self._test_unpack("tarfile.tar.xz")

    def test_cleanup(self):
        files = [
            UnpackedFile(os.path.join(TEST_DIR, "zipfile.zip"), "zipfile.zip"),
        ]

        with unpack_files(files) as unpacked_files:
            self.assertTrue(all(map(lambda x: os.path.exists(x.path), unpacked_files)))

        self.assertFalse(any(map(lambda x: os.path.exists(x.path), unpacked_files)))  # check all files dropped
