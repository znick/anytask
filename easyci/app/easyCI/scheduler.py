import json
import logging
import os
import requests

# TODO: move to environment variables
#from settings_local import GITHUB_TOKEN, \
#    GITHUB_USER, GITHUB_REPO, GITHUB_ORG, GITHUB_WORKFLOW

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_USER = os.environ.get("GITHUB_USER")
GITHUB_REPO = os.environ.get("GITHUB_REPO")
GITHUB_ORG = os.environ.get("GITHUB_ORG")
GITHUB_WORKFLOW = os.environ.get("GITHUB_WORKFLOW")
GITLAB_TRIGGER_TOKEN = os.environ.get("GITLAB_TRIGGER_TOKEN")
GITLAB_READ_PIPELINES_TOKEN = os.environ.get("GITLAB_READ_PIPELINES_TOKEN")


class AbstractScheduler:
    def __init__(self):
        pass

    def schedule(self):
        raise NotImplementedError("attempt to run abstract worker.")


class GithubActionsScheduler(AbstractScheduler):
    def __init__(self, *args):
        super().__init__(*args)

    def schedule(self, task, repo, run_cmd, files, docker_image, timeout):
        inputs = {"task" : task,
                  "repo" : repo,
                  "run_cmd" : run_cmd,
                  "files" : json.JSONEncoder().encode(files),
                  "docker_image" : docker_image,
                  "timeout" : timeout}
        data = {"ref" : "master", "inputs" : inputs}
        headers = {"Accept" : "application/vnd.github.v3+json"}
        url = "https://api.github.com/repos/{}/{}/actions/workflows/{}/" \
              "dispatches".format(GITHUB_ORG, GITHUB_REPO, GITHUB_WORKFLOW)
        auth = (GITHUB_USER, GITHUB_TOKEN)
        r = requests.post(url, data=json.JSONEncoder().encode(data),
                headers=headers, auth=auth)


class GitlabCIScheduler(AbstractScheduler):
    def __init__(self, *args):
        super().__init__(*args)

    def schedule(self, task, repo, run_cmd, files, docker_image, timeout):
        inputs = {"TASK" : task,
                  "REPO" : repo,
                  "RUN_CMD" : run_cmd,
                  "FILES" : json.JSONEncoder().encode(files),
                  "DOCKER_IMAGE" : docker_image,
                  "TIMEOUT" : timeout}
        variables = "".join(["&variables[{}]={}".format(key, inputs[key])
            for key in inputs])
        url = "https://gitlab.com/api/v4/projects/25597841/ref/master" \
        "/trigger/pipeline?token={}&{}".format(GITLAB_TRIGGER_TOKEN, variables)
        print(url)
        r = requests.post(url)

    def get_info(self):
        url = "https://gitlab.com/api/v4/projects/25597841/pipelines"
        headers = {"PRIVATE-TOKEN" : GITLAB_READ_PIPELINES_TOKEN }
        return requests.get(url, headers=headers)

