import json
import logging
import requests

from settings_local import GITHUB_TOKEN, \
    GITHUB_USER, GITHUB_REPO, GITHUB_ORG, GITHUB_WORKFLOW


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
        return r

