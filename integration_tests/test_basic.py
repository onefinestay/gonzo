from contextlib import contextmanager

from fabric.api import run, settings, sudo
from mock import patch

from gonzo.tasks.pip import index_url
from gonzo.tasks.release import (
    activate, list_releases, project_path, prune, push, usudo,
    virtualenv)


@contextmanager
def log_sudo_calls():
    with patch('gonzo.tasks.release.sudo') as mock_sudo:
        log = []
        def capturing_sudo(*a, **k):
            log.append((a, k))
            return sudo(*a, **k)
        mock_sudo.side_effect = capturing_sudo
        yield log


def test_separate_venv(container, test_repo):
    # small package with no requirements
    test_repo.files['requirements.txt'] = 'initools==0.2'
    pip_output = push()
    setup_output = 'Running setup.py install for initools'
    assert setup_output in pip_output
    activate()
    # trigger commit
    test_repo.files['dummy'] = 'a'
    pip_output = push()
    assert setup_output in pip_output


def test_custom_index_url(container, test_repo):
    test_repo.files['requirements.txt'] = 'initools==0.2'
    index_url('https://pypi.python.org/simple/')
    with log_sudo_calls() as log:
        push()
    pip_install_args, _ = log[-1]
    (install_cmd,) = pip_install_args
    assert '--index-url=https://pypi.python.org/simple/' in install_cmd


def test_pruning(container, test_repo):
    project_dir = project_path('releases')
    venv_dir = project_path('virtualenvs')

    test_repo.files['requirements.txt'] = 'initools==0.2'
    push()
    activate()
    # trigger commit
    test_repo.files['dummy'] = 'a'
    push()
    activate()

    history = list_releases()
    assert len(history) == 2

    def ls(path):
        return run('ls {}'.format(path)).split()

    releases = ls(project_dir)
    virtualenvs = ls(venv_dir)

    assert len(releases) == 3  # includes current
    assert len(virtualenvs) == 3  # includes current

    prune(keep=1)

    history = list_releases()
    assert len(history) == 1

    releases = ls(project_dir)
    virtualenvs = ls(venv_dir)

    assert len(releases) == 2  # includes current
    assert len(virtualenvs) == 2  # includes current

    # check that virtualenv still works
    with virtualenv():
        with settings(warn_only=True):
            res = usudo('pip freeze|grep -i initools')
        assert res.succeeded
