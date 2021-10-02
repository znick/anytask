import io
import json
import logging
import os
import shutil
import subprocess
import threading

from contextlib import contextmanager
from urllib.request import urlretrieve

logging.basicConfig(level=logging.DEBUG)

TASK_DIR = "task"
GIT_DIR = "git"

BUF_SIZE = 4096
LIMIT_BYTES = 10 * 1024 * 1024
MAX_COMMENT_SIZE = 10000


def git_clone(repo, dst_dir):
    cmd = ["git", "clone", repo, dst_dir]

    ssh_key = os.environ.get("SSH_KEY")
    ssh = "ssh -o StrictHostKeyChecking=no -vvv"
    if ssh_key:
#        subprocess.check_call(["chmod", "0600", ssh_key])
        ssh += " -i '{}'".format(ssh_key)

    env = os.environ.copy()
    env["GIT_SSH_COMMAND"] = ssh

    logging.info("RUN: %s", cmd)
    logging.info("ENV: %s", env)
    subprocess.check_call(cmd, env=env)


def prepare_dir(repo, files, dirname="./"):
    git_dir = os.path.join(dirname, GIT_DIR)
    task_dir = os.path.join(dirname, TASK_DIR)
    git_clone(repo, git_dir)

    os.mkdir(task_dir)
    for url in files:
        # TODO: do it using os
        filename = url.split('/')[-1]
        dst_path = os.path.join(task_dir, filename)
        logging.info("Download '%s' -> '%s'", url, dst_path)
        urlretrieve(url, dst_path)


def limited_reader(fn_in, fn_out, limit_bytes):
    fn = io.open(fn_in.fileno(), encoding="utf-8")
    read_bytes = 0
    truncated = False
    try:
        while True:
            buf = fn.read(BUF_SIZE)
            if len(buf) == 0:
                break

            if read_bytes >= limit_bytes and not truncated:
                fn_out.write("\nTRUNCATED\n")
                truncated = True

            read_bytes += len(buf)
            if not truncated:
                fn_out.write(buf)
    except Exception as e:
        fn_out.write("Error while read or write proccess output: {}".format(e))


class Worker:
    def __init__(self, task, repo, run_cmd, files, timeout, output_file,
            course_id, issue_id):
        self.task = task
        self.repo = repo
        self.run_cmd = run_cmd
        self.files = files
        self.timeout = timeout
        self.output_file = output_file
        self.course_id = course_id
        self.issue_id = issue_id

    def run(self):
        logging.info("Process task %s", self.task)
        prepare_dir(self.repo, self.files)
        run_cmd = [self.run_cmd] + [self.task, "../"+TASK_DIR]
        output, ret = self.execute(run_cmd, cwd=GIT_DIR)
        self.make_artifact(output)
        self.log_output(ret)

    def execute(self, cmd, cwd='./'):
        if self.timeout is not None and \
                not isinstance(self.timeout, (float, int)):
            raise TypeError('timeout argument is not a float')

        command = []
        if self.timeout:
            command += ['timeout', '-k', str(self.timeout + 1), 
                    str(self.timeout)]
        command += cmd

        p = subprocess.Popen(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                cwd=cwd)

        output = io.StringIO()
        t1 = threading.Thread(
                target=limited_reader, 
                args=(p.stdout, output, LIMIT_BYTES))
        t2 = threading.Thread(
                target=limited_reader, 
                args=(p.stderr, output, LIMIT_BYTES))

        t1.start()
        t2.start()

        t1.join()
        t2.join()
        p.wait()

        status = p.returncode
        output = output.getvalue()
        is_timeout = status == 124

        ret = dict()
        ret["status"] = status == 0 and not is_timeout
        ret["retcode"] = status
        ret["is_timeout"] = is_timeout
        ret["output"] = output
        ret["course_id"] = self.course_id
        ret["issue_id"] = self.issue_id

        return json.dumps(ret), ret

    def make_artifact(self, output):
        with open(self.output_file, 'w') as f:
            f.write(output)

    def log_output(self, ret):
        status = "failure"
        if ret["status"]:
            status = "success"

        logging.info(" Task {} done, status: {}, retcode: {}, is_timeout: {}".format(
            self.task, status, ret["retcode"], ret["is_timeout"]
        ))

        if len(ret["output"]) > MAX_COMMENT_SIZE:
            ret["output"] = ret["output"][:MAX_COMMENT_SIZE]
            ret["output"] += "\n...\nTRUNCATED\n"

        if ret["is_timeout"]:
            ret["output"] += "\nTIMEOUT ({} sec)\n".format(ret["timeout"])

        message = "\n == Task output start\n"
        message += ret["output"]
        message += " == Task output end\n"

        logging.info(message)
        return message
