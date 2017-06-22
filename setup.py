
import distutils
import os

from setuptools import setup, find_packages
#from distutils.core import setup

def findall(dir = os.curdir):
    """Find all files under 'dir' and return the list of full filenames
    (relative to 'dir').
    """
    all_files = []
    for base, dirs, files in os.walk(dir, followlinks=True):
        if base==os.curdir or base.startswith(os.curdir+os.sep):
            base = base[2:]
        if base:
            files = [os.path.join(base, f) for f in files]
        all_files.extend(filter(os.path.isfile, files))
    return all_files # noqa

distutils.filelist.findall = findall    # fix findall bug in distutils.

setup(name='Anytask',
      setup_requires = [ "setuptools_git >= 0.3" ],
      packages=find_packages(),
      include_package_data=True,
)
