import os
import requests_mock
import unittest.mock as mock
from requests_mock_flask import add_flask_app_to_mock
import pytest

os.environ["GITLAB_REPO_ID"] = "777"
os.environ["GITLAB_TRIGGER_TOKEN"] = "000"


def my_open(filename):
    if filename == 'config.json':
        content = "[ " \
                  "{\"host\": \"https://anytask.org\"," \
                  "\"course_id\": 1," \
                  "\"repo\": \"git@github.com:tswr/imkn_python_method.git\"," \
                  "\"run_cmd\": [\"ls\"]," \
                  "\"docker_image\": \"zhnick/imkn_python_checker:latest\"," \
                  "\"timeout\": 10800}]"
    elif filename == 'passwords.json':
        content = "{ \"http://localhost:8119\": {" \
                  "\"username\": \"admin\"," \
                  "\"password\": \"qwerty\"} }"
    else:
        raise FileNotFoundError(filename)
    file_object = mock.mock_open(read_data=content).return_value
    file_object.__iter__.return_value = content.splitlines(True)
    return file_object


@pytest.fixture(scope="session")
def setup_with_mock():
    with requests_mock.Mocker() as resp_m, mock.patch('app.easyCI.schedule_task.open', new=my_open):
        from app import create_app
        from gitlabMock import gitlab_mock_app
        add_flask_app_to_mock(
            mock_obj=resp_m,
            flask_app=gitlab_mock_app,
            base_url='https://gitlab.com',
        )
        easyci_app = create_app()
        return easyci_app, gitlab_mock_app


