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


def gitlabci_getter(url_constructor):
    def wrapper(*args, **kwargs):
        url = url_constructor(*args, **kwargs)
        headers = {"PRIVATE-TOKEN" : GITLAB_READ_PIPELINES_TOKEN }
        request = requests.get(url, headers=headers)
        return json.loads(request.content.decode())
    return wrapper


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

    @gitlabci_getter
    def get_pipelines(self):
        return self.prefix + "/pipelines"

    @gitlabci_getter
    def get_pipeline(self, pipeline_id):
        return self.prefix + "/pipelines/{}".format(pipeline_id)

    def get_pipeline_vars(self, pipeline_id):
        vars_raw = self._get_pipeline_vars_raw(pipeline_id)
        # vars_raw = list of {"key" : <var_name>, "value" : <var_value>, ...}
        get_var = lambda x: [i for i in vars_raw if i["key"] == x][0]["value"]
        vars_new = dict()
        for var in vars_raw:
            vars_new[var["key"]] = var["value"]
        return vars_new

    @gitlabci_getter
    def _get_pipeline_vars_raw(self, pipeline_id):
        return self.prefix + "/pipelines/{}/variables".format(pipeline_id)

    @gitlabci_getter
    def get_job_artifact(self, job_id):
        return self.prefix + "/jobs/{}/artifacts/{}".format(
                job_id, self.output_file)

