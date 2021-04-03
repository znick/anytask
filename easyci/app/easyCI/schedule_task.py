import json
import requests
import tempfile
import shutil
import subprocess
import os
import logging
import urllib.request

from multiprocessing import Pool

from app.easyCI.scheduler import GitlabCIScheduler
import app.easyCI.docker as docker

from contextlib import contextmanager

LOG = logging.getLogger(__name__)
CONFIG = "config.json"
PASSWORDS = "passwords.json"
MAX_COMMENT_SIZE = 10000
REQUEST_TIMEOUT = 300


# TODO:
#def send_message(ret, qtask):
def send_message(ret):
    print(ret)
    return

    status, retcode, is_timeout, output = ret

    LOG.info("Task %d done, status:%s, retcode:%d, is_timeout:%d",
                 qtask.id, status, retcode, is_timeout)

    LOG.info(" == Task %d output start", qtask.id)
    for line in output.split("\n"):
        LOG.info(line)
    LOG.info(" == Task %d output end", qtask.id)

    if len(output) > MAX_COMMENT_SIZE:
        output = output[:MAX_COMMENT_SIZE]
        output += u"\n...\nTRUNCATED"

    if is_timeout:
        output += u"\nTIMEOUT ({} sec)".format(qtask.course["timeout"])
    comment = u"[id:{}] Check DONE!<br>\nSubmited on {}<br>\n<pre>{}</pre>\n".format(qtask.id,
                                                                                 qtask.event_timestamp,
                                                                                 output)
    LOG.info("{}/api/v1/issue/{}/add_comment".format(qtask.host, qtask.issue_id))
    response = requests.post("{}/api/v1/issue/{}/add_comment".format(qtask.host, qtask.issue_id),
                             auth=qtask.auth, data={"comment":comment.encode("utf-8")}, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    LOG.info(" == Task %d DONE!, URL: %s/issue/%d", qtask.id, qtask.host, qtask.issue_id)

    return qtask


def load_passwords(filename=PASSWORDS):
    with open(filename) as config_fn:
        return json.load(config_fn)


def load_config(filename=CONFIG):
    with open(filename) as config_fn:
        config_arr = json.load(config_fn)
        config_dict = {}
        for course in config_arr:
            config_dict[course["course_id"]] = course

        return config_dict


def get_auth(passwords, host):
    host_auth = passwords[host]
    return host_auth["username"], host_auth["password"]


config = load_config()
passwords = load_passwords()

# FIXME: remove GitlabCI hardcoding
scheduler = GitlabCIScheduler()


def course_exists(course_id):
    return course_id in config


def add_to_scheduler(task):
    course_id = task["course_id"]
    course = config[course_id]
    scheduler.schedule(task["title"], course["repo"],
                       " ".join(course["run_cmd"]),
                       task["files"], course["docker_image"], course["timeout"])
