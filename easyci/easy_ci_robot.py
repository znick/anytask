#!/usr/bin/env python

import json
import requests
import re
import logging
import tempfile
import shutil
import subprocess
import os
import sys
import urllib
from multiprocessing import Pool

import docker

from collections import OrderedDict
from contextlib import contextmanager

CONFIG = "config.json"
PASSWORDS = "passwords.json"
MAX_COMMENT_SIZE = 10000
PROCS = 2
REQUEST_TIMEOUT = 180

logging.basicConfig(format="%(asctime)-15s %(name)s %(process)d %(message)s", level=logging.DEBUG)


class QueueTask(object):
    host = None
    auth = None
    config = None
    id = None
    course = None
    task = None
    issue = None
    event = None
    files = None

    def __repr__(self):
        return repr(self.__dict__)


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


def prepare_dir(qtask, dirname):
    git_dir = os.path.join(dirname, "git")
    task_dir = os.path.join(dirname, "task")
    git_clone(qtask.course["repo"], git_dir)

    os.mkdir(task_dir)
    for f in qtask.files:
        url = f["url"]
        filename = url.split('/')[-1]
        dst_path = os.path.join(task_dir, filename)

        logging.info("Download '%s' -> '%s'", url, dst_path)
        urllib.urlretrieve(url, dst_path)


def proccess_task(qtask):
    logging.info("Proccess task %s", qtask.id)
    with tmp_dir() as dirname:
        prepare_dir(qtask, dirname)

        run_cmd = qtask.course["run_cmd"] + [qtask.task["title"], "/task_dir/task"]
        #run_cmd = ["ls", "/task_dir/task"]
        ret = docker.execute(run_cmd, cwd="/task_dir/git", timeout=qtask.course["timeout"], user='root',
                             network='bridge', image=qtask.course["docker_image"],
                             volumes=["{}:/task_dir:ro".format(os.path.abspath(dirname))])

        status, retcode, is_timeout, output = ret

        logging.info("Task %d done, status:%s, retcode:%d, is_timeout:%d",
                     qtask.id, status, retcode, is_timeout)

        logging.info(" == Task %d output start", qtask.id)
        for line in output.split("\n"):
            logging.info(line)
        logging.info(" == Task %d output end", qtask.id)

        if len(output) > MAX_COMMENT_SIZE:
            output = output[:MAX_COMMENT_SIZE]
            output += u"\n...\nTRUNCATED"

        if is_timeout:
            output += u"\nTIMEOUT ({} sec)".format(qtask.course["timeout"])

        comment = u"[id:{}] Check DONE!<br>\nSubmited on {}<br>\n<pre>{}</pre>\n".format(qtask.id,
                                                                                     qtask.event["timestamp"],
                                                                                     output)

        response = requests.post("{}/api/v1/issue/{}/add_comment".format(qtask.host, qtask.issue["id"]),
                                 auth=qtask.auth, data={"comment":comment.encode("utf-8")}, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        logging.info(" == Task %d DONE!, URL: %s/issue/%d", qtask.id, qtask.host, qtask.issue["id"])
        return qtask


def load_config(filename=CONFIG):
    with open(filename) as config_fn:
        return json.load(config_fn)


def get_auth(passwords, host):
    host_auth = passwords[host]
    return (host_auth["username"], host_auth["password"])


DONE_MESSAGE_RE = re.compile(r'\[id:(\d+)\] Check DONE!')
def make_queue(config, passwords):
    queue = OrderedDict()
    for course in config:
        course_id = course["course_id"]
        auth = get_auth(passwords, course["host"])
        response = requests.get("{}/api/v1/course/{}/issues?add_events=1".format(course["host"], course_id),
                                auth=auth, timeout=REQUEST_TIMEOUT)
        if response.status_code != 200:
            logging.error("Course %d has non-200 reply. Skipped", course["course_id"])
            continue

        for issue in response.json():
            for event in issue.get("events", []):
                if event["author"]["username"] == auth[0]:
                    m = DONE_MESSAGE_RE.search(event["message"])
                    if m:
                        done_id = int(m.group(1))
                        queue.pop(done_id, None)
                    continue

                files = event.get("files")
                if not files:
                    continue

                qtask = QueueTask()
                qtask.host = course["host"]
                qtask.auth = auth
                qtask.config = config
                qtask.course = course
                qtask.task = issue["task"]
                qtask.issue = issue
                qtask.event = event
                qtask.files = files
                qtask.id = event["id"]

                queue[qtask.id] = qtask

    return queue


def main():
    logging.info("Start parallel version!")
    config = load_config()
    passwords = load_config(PASSWORDS)
    queue = make_queue(config, passwords)
    pool = Pool(processes=PROCS)

    logging.info("Queue:")
    for qtask in queue.itervalues():
        logging.info("%s\t%s\t%s\t%s\t%s\t%s", qtask.host, qtask.course["course_id"], qtask.id, qtask.task["title"],
                     qtask.issue["student"]["username"], "{}/issue/{}".format(qtask.host, qtask.issue["id"]))
    if "--only_queue" in sys.argv:
        sys.exit(0)

    for qtask in pool.imap_unordered(proccess_task, queue.itervalues()):
        logging.info(" == Parralel Task %d DONE!, URL: %s/issue/%d", qtask.id, qtask.host, qtask.issue["id"])

    logging.info("All DONE!")

if __name__ == "__main__":
    main()
