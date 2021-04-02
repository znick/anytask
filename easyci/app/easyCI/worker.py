import logging
import os
import shutil
import subprocess
import tempfile

from contextlib import contextmanager
from urllib.request import urlretrieve

# custom
import docker

TASK_DIR = "task"
GIT_DIR = "git"
DOCKER_WORKDIR = "/task_dir"
DOCKER_TASK_DIR = '/'.join((DOCKER_WORKDIR, TASK_DIR))
DOCKER_GIT_DIR = '/'.join((DOCKER_WORKDIR, GIT_DIR))


@contextmanager
def tmp_dir():
    t = tempfile.mkdtemp(dir="/var/tmp")
    try:
        yield t
    finally:
        shutil.rmtree(t)


def git_clone(repo, dst_dir):
    cmd = ["git", "clone", repo, dst_dir]
    logging.info("RUN: %s", cmd)
    subprocess.check_call(cmd)


def prepare_dir(repo, files, dirname="./"):
    git_dir = os.path.join(dirname, GIT_DIR)
    task_dir = os.path.join(dirname, TASK_DIR)
    git_clone(repo, git_dir)

    os.mkdir(task_dir)
    for url in files:
        # FIXME: do it using os
        filename = url.split('/')[-1]
        dst_path = os.path.join(task_dir, filename)
        logging.info("Download '%s' -> '%s'", url, dst_path)
        urlretrieve(url, dst_path)


class Worker:
    def __init__(self, task, repo, run_cmd, files, docker_image, timeout):
        self.task = task
        self.repo = repo
        self.run_cmd = run_cmd
        self.files = files
        self.docker_image = docker_image
        self.timeout = timeout
        logging.info("init finished")

    def run(self):
        logging.info("Proccess task %s", self.task)
        with tmp_dir() as dirname:
            prepare_dir(self.repo, self.files, dirname)
            run_cmd = [self.run_cmd] + [self.task, DOCKER_TASK_DIR]
            ret = docker.execute(
                    run_cmd,
                    cwd=DOCKER_GIT_DIR, 
                    timeout=self.timeout, 
                    user='root',
                    network='bridge', 
                    image=self.docker_image,
                    volumes=["{}:{}:ro".format(
                        os.path.abspath(dirname), DOCKER_WORKDIR)])

            return ret
