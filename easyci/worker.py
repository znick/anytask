import requests
import json

from settings_local import GITHUB_TOKEN, \
    GITHUB_USER, GITHUB_REPO, GITHUB_ORG, GITHUB_WORKER


class AbstractWorker:
    def __init__(self, auth, task, repo, run_cmd, files, docker_image, timeout):
        self.auth = auth
        self.task = task
        self.repo = repo
        self.run_cmd = run_cmd
        self.files = files
        self.docker_image = docker_image
        self.timeout = str(timeout)

    def run(self):
        raise NotImplementedError("attempt to run abstract worker.")


class GithubActionsWorker(AbstractWorker):
    def __init__(self, *args):
        super().__init__(*args)

    def run(self):
        inputs = {"task" : self.task,
                "repo" : self.repo,
                "run_cmd" : self.run_cmd,
                "docker_image" : self.docker_image,
                "timeout" : self.timeout}
        data = {"ref" : "master", "inputs" : inputs}
        headers = {"Accept" : "application/vnd.github.v3+json"}
        url = "https://api.github.com/repos/{}/{}/actions/workflows/{}/" \
              "dispatches".format(GITHUB_ORG, GITHUB_REPO, GITHUB_WORKER)
        auth = (GITHUB_USER, GITHUB_TOKEN)
        r = requests.post(url, data=json.JSONEncoder().encode(data),
                headers=headers, auth=auth)
        return r

    def assert_repo_form(self):
        # TODO: check if 'repo' has form '<owner>/<repo_name>'
        # throw TypeError if it does not
        return True
