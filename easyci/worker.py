from secrets import GITHUB_TOKEN


class AbstractWorker:
    def __init__(self, auth, task, repo, run_cmd, files, docker_image, timeout):
        self.auth = auth
        self.task = task
        self.repo = repo
        self.run_cmd = run_cmd
        self.files = files
        self.docker_image = docker_image
        self.timeout = timeout

    def run(self):
        raise NotImplementedError("attempt to run abstract worker.")


class GithubActionsWorker(AbstractWorker):
    def __init__(self, args*):
        super().__init__(args*)

    def run(self):
        assert_repo_form()

    def assert_repo_form(self):
        # TODO: check if 'repo' has form '<owner>/<repo_name>'
        # throw TypeError if it does not
        return True
