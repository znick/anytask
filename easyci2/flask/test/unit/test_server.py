def test_server_correct(setup_with_mock):
    easyci_app, gitlab_mock_app = setup_with_mock
    client = easyci_app.test_client()
    response = client.post('/api/add_task',
                           json={
                               "course_id": 1,
                               "title": "Test_task",
                               "issue_id": 2,
                               "files": [
                                   "https://raw.githubusercontent.com/znick/anytask/master/anytask/anyrb/test_data/1.py"]
                           })
    assert (response.status_code == 202)


def test_server_incorrect(setup_with_mock):
    easyci_app, gitlab_mock_app = setup_with_mock
    client = easyci_app.test_client()
    response_without_title = client.post('/api/add_task',
                           json={
                               "course_id": 1,
                               "issue_id": 2,
                               "files": [
                                   "https://raw.githubusercontent.com/znick/anytask/master/anytask/anyrb/test_data/1.py"]
                           })
    response_without_course_id = client.post('/api/add_task',
                                         json={
                                             "title": "Test_task",
                                             "issue_id": 2,
                                             "files": [
                                                 "https://raw.githubusercontent.com/znick/anytask/master/anytask/anyrb/test_data/1.py"]
                                         })
    response_without_issue_id = client.post('/api/add_task',
                                             json={
                                                 "title": "Test_task",
                                                 "course_id": 1,
                                                 "files": [
                                                     "https://raw.githubusercontent.com/znick/anytask/master/anytask/anyrb/test_data/1.py"]
                                             })
    response_without_files = client.post('/api/add_task',
                                            json={
                                                "title": "Test_task",
                                                "course_id": 1,
                                                "issue_id": 2,
                                               })
    assert (response_without_title.status_code == 400)
    assert (response_without_course_id.status_code == 400)
    assert (response_without_files.status_code == 400)
    assert (response_without_issue_id.status_code == 400)
