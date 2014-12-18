from gonzo.tasks.release import activate, list_releases, push


def test_basic(container, test_repo):
    # small package with no requirements
    test_repo.files['requirements.txt'] = 'initools==0.2'
    pip_output = push()
    setup_output = 'Running setup.py install for initools'
    assert setup_output in pip_output
    activate()
    # trigger commit
    test_repo.files['dummy'] = 'a'
    pip_output = push()
    assert setup_output not in pip_output
    activate()
    # trigger commit
    test_repo.files['dummy'] = 'b'
    push()
    history = list_releases()
    assert len(history) == 2


def test_separate_venv(container, test_repo):
    # small package with no requirements
    test_repo.files['requirements.txt'] = 'initools==0.2'
    pip_output = push(separate_venv=True)
    setup_output = 'Running setup.py install for initools'
    assert setup_output in pip_output
    activate()
    # trigger commit
    test_repo.files['dummy'] = 'a'
    pip_output = push(separate_venv=True)
    assert setup_output in pip_output
