import json
import requests
import tempfile
import shutil
import subprocess
import os
import logging
import urllib.request

from multiprocessing import Pool
from contextlib import contextmanager

from app.easyCI.scheduler import GitlabCIScheduler


LOG = logging.getLogger(__name__)
CONFIG = "config.json"
PASSWORDS = "passwords.json"
PASSWORDS_JSON = os.environ.get("PASSWORDS_JSON")
MAX_COMMENT_SIZE = 10000
REQUEST_TIMEOUT = 300
SSH_KEY_ID_DEFAULT = 'SSH_KEY'


def load_passwords(filename=PASSWORDS):
    if PASSWORDS_JSON is not None:
        return json.loads(PASSWORDS_JSON)

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


passwords = {}
config = {}


def setup_configs():
    global passwords, config
    config = load_config()
    passwords = load_passwords()


scheduler = GitlabCIScheduler()


def course_exists(course_id):
    return course_id in config


def add_to_scheduler(task):
    course_id = task["course_id"]
    course = config[course_id]
    issue_id = task["issue_id"]
    scheduler.schedule(
            task["title"], 
            course["repo"],
            course["run_cmd"],
            task["files"], 
            course["docker_image"],
            course["timeout"],
            course_id,
            issue_id,
            course.get('ssh_key_id', SSH_KEY_ID_DEFAULT))


def send_message(ret):
    job_id = ret["job_id"]
    timestamp = ret["timestamp"]
    pipeline_url = ret["pipeline_url"]
    job_status = ret["job_status"]

    course_id = ret["course_id"]
    issue_id = ret["issue_id"]

    # if job_status == "success", we have these 4 fields
    status = ret["status"]
    retcode = ret["retcode"]
    is_timeout = ret["is_timeout"]
    output = ret["output"]

    print(config)
    course = config[course_id]
    host = course["host"]
    auth = get_auth(passwords, host)
    timeout = course["timeout"]

#    LOG.info("Task %d done, status:%s, retcode:%d, is_timeout:%d",
#                 qtask.id, status, retcode, is_timeout)
#
#    LOG.info(" == Task %d output start", qtask.id)
#    for line in output.split("\n"):
#        LOG.info(line)
#    LOG.info(" == Task %d output end", qtask.id)

    if job_status == "success":
        if len(output) > MAX_COMMENT_SIZE:
            output = output[:MAX_COMMENT_SIZE]
            output += u"\n...\nTRUNCATED"

        if is_timeout:
            output += u"\nTIMEOUT ({} sec)".format(timeout)

    if output is None:
        output = ''

    comment = u"[id:{}] Job status: {}. Status: {}<br>\n" \
               "Submited on {}<br>\n<pre>{}</pre><br>\n" \
               "See <a href={}>your task</a> in the CI" \
              .format(job_id, job_status, status,
                      timestamp, output,
                      pipeline_url)

    print("comment:", comment)
#
#    LOG.info("{}/api/v1/issue/{}/add_comment".format(qtask.host, qtask.issue_id))

    url = "{}/api/v1/issue/{}/add_comment".format(host, issue_id)
    print(url)
    response = requests.post(url, auth=auth,
            data={"comment":comment.encode("utf-8")}, 
            timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

#    LOG.info(" == Task %d DONE!, URL: %s/issue/%d", qtask.id, qtask.host, qtask.issue_id)
#
#    return qtask
