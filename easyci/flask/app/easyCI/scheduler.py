import json
import logging
import os
import requests

GITLAB_REPO_ID = os.environ.get("GITLAB_REPO_ID")
GITLAB_TRIGGER_TOKEN = os.environ.get("GITLAB_TRIGGER_TOKEN")
GITLAB_READ_PIPELINES_TOKEN = os.environ.get("GITLAB_READ_PIPELINES_TOKEN")


class AbstractScheduler:
    def __init__(self):
        pass

    def schedule(self):
        raise NotImplementedError("attempt to run abstract worker.")


class GitlabCIScheduler(AbstractScheduler):
    output_file = "run.log"

    def __init__(self, *args):
        super().__init__(*args)
        self.prefix = "https://gitlab.com/api/v4/projects/" + GITLAB_REPO_ID

    def schedule(self, task, repo, run_cmd, files, docker_image, timeout, 
            course_id, issue_id):
        inputs = {"TASK" : task,
                  "REPO" : repo,
                  "RUN_CMD" : run_cmd,
                  "FILES" : json.JSONEncoder().encode(files),
                  "DOCKER_IMAGE" : docker_image,
                  "TIMEOUT" : timeout,
                  "OUTPUT_FILE" : self.output_file,
                  "COURSE_ID" : course_id,
                  "ISSUE_ID" : issue_id}
        variables = "".join(["&variables[{}]={}".format(key, inputs[key])
            for key in inputs])
        url = self.prefix + "/ref/master/trigger/pipeline?token={}&{}".format(
                    GITLAB_TRIGGER_TOKEN, variables)
        r = requests.post(url)

    def get_pipelines(self):
        url = self.prefix + "/pipelines"
        headers = {"PRIVATE-TOKEN" : GITLAB_READ_PIPELINES_TOKEN }
        request = requests.get(url, headers=headers)
        return json.loads(request.content.decode())

    def get_pipeline_vars(self, pipeline_id):
        url = self.prefix + "/pipelines/{}/variables".format(pipeline_id)
        headers = {"PRIVATE-TOKEN" : GITLAB_READ_PIPELINES_TOKEN }
        request = requests.get(url, headers=headers)
        return json.loads(request.content.decode())

    def get_job_artifact(self, job_id):
        url = self.prefix + "/jobs/{}/artifacts/{}".format(
                job_id, self.output_file)
        headers = {"PRIVATE-TOKEN" : GITLAB_READ_PIPELINES_TOKEN }
        request = requests.get(url, headers=headers)
        return json.loads(request.content.decode())
