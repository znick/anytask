#!/usr/bin/python

import os
import sys
import venv
import argparse

from config import *


def report(msg, prefix=REPORT_PREFIX):
    print(prefix, msg)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--workdir", default=WORKDIR_DEFAULT,
            help="Deploy working directory")
    parser.add_argument("-p", "--python-path", default=PYTHON_PATH_DEFAULT,
            help="Path to python interpreter")
    
    return parser.parse_args()


def create_workdir(workdir):
    if not os.path.exists(workdir):
        report("Create workdir {}".format(workdir))
        os.mkdir(workdir)
    elif not os.path.isdir(workdir):
        raise FileExistsError(
                "{} already exists and is not a directory.".format(workdir))


def clone_repo():
    report("Cloning repository")
    os.system("git clone {}".format(ANYTASK_REPO))
    os.chdir(ANYTASK_DIR)
    os.system("git submodule init")
    os.system("git submodule update")
    os.chdir(os.path.basename(os.getcwd()))


def enable_venv():
    report("Enable environment")
    env = venv.EnvBuilder(with_pip=True)
    env.create(VENV_NAME)


def main():
    compatible = True
    if sys.version_info < (3, 3):
        compatible = False
    elif not hasattr(sys, 'base_prefix'):
        compatible = False
    if not compatible:
        raise ValueError('This script is only for use with '
                         'Python 3.3 or later')

    args = parse_args()
    workdir = args.workdir
    python_path = args.python_path

    create_workdir(workdir)
    os.chdir(workdir)
    clone_repo()
    enable_venv()

if __name__ == "__main__":
    main()
