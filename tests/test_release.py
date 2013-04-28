from contextlib import contextmanager, nested
import copy
import re

from mock import patch

from gonzo.tasks.release import (
    get_releases, get_previous_release, append_to_history, rollback_history)


@contextmanager
def disable_remote_commands():
    with nested(
        patch('gonzo.tasks.release.local'),
        patch('gonzo.tasks.release.run'),
        patch('gonzo.tasks.release.sudo'),
    ) as (local, run, sudo):
        local.side_effect = RuntimeError("'local' called during testing")
        run.side_effect = RuntimeError("'run' called during testing")
        sudo.side_effect = RuntimeError("'sudo' called during testing")

        yield


@contextmanager
def mock_history(initial):
    """ intercept ``sudo`` and ``run`` commands, and match against
        a list of regexes, to fake history management
    """

    releases = copy.copy(initial)
    project = 'project'
    history_file = '/srv/{}/releases/.history'.format(project)

    def exists(filename):
        if filename == history_file:
            return (releases is not None)
        else:
            raise RuntimeError('Unknown file "{}"'.format(filename))

    def list_releases():
        return '\n'.join(releases)

    def append_release(release):
        releases.append(release)

    def rollback():
        if releases is None:
            raise RuntimeError("Trying to rollback with missing history file")
        if releases:  # sed is ok as long as the file exists
            releases.pop()

    dispatch = {
        "cat {history_file}": list_releases,
        "echo (\w+) >> {history_file}": append_release,
        r"sed -i '\$ d' {history_file}": rollback,
    }

    def run(cmd, **kwargs):
        for regex, callback in dispatch.items():
            regex = regex.format(history_file=history_file)
            match = re.match(regex, cmd)
            if match:
                return callback(*match.groups())
        raise RuntimeError('Uncaught command "{}"'.format(cmd))

    with nested(
        patch('gonzo.tasks.release.run', side_effect=run),
        patch('gonzo.tasks.release.sudo', side_effect=run),
        patch('gonzo.tasks.release.exists', side_effect=exists),
        patch('gonzo.tasks.release.get_project'),
    ) as (run, sudo, exists, get_project):

        get_project.return_value = project
        yield releases


# @contextmanager
# def mock_history(initial=None):
    # if initial is None:
        # initial = []

    # releases = initial[:]

    # with nested(
        # patch('gonzo.tasks.release.get_releases'),
        # patch('gonzo.tasks.release.append_to_history'),
        # patch('gonzo.tasks.release.rollback_history'),
    # ) as (get, append, rollback):

        # get.return_value = releases
        # append.side_effect = lambda rel: releases.append(rel)
        # rollback.side_effect = lambda: releases.pop()

        # with disable_remote_commands():
            # yield releases


@patch('gonzo.tasks.release.get_releases')
def test_get_previous_release(get_releases):
    releases = [
        'aaa',
        'bbb',
        'ccc',
        'ddd',
    ]

    get_releases.return_value = releases

    assert get_previous_release('ccc') == 'bbb'
    assert get_previous_release(None) is None
    assert get_previous_release('aaa') is None
    assert get_previous_release('xxx') is None


@patch('gonzo.tasks.release.get_releases')
def test_get_previous_release_ho_history(get_releases):
    releases = []

    get_releases.return_value = releases

    assert get_previous_release(None) is None
    assert get_previous_release('xxx') is None


def test_get_releases():
    with mock_history(initial=['aaa', 'bbb']):
        assert get_releases() == ['aaa', 'bbb']


def test_get_releases_empty():
    with mock_history(initial=[]):
        assert get_releases() == []


def test_get_releases_missing():
    with mock_history(initial=None):
        assert get_releases() == []


def test_append_to_history():
    with mock_history(initial=['aaa']) as releases:
        append_to_history('bbb')
        assert releases == ['aaa', 'bbb']


def test_append_to_history_empty():
    with mock_history(initial=[]) as releases:
        append_to_history('aaa')
        assert releases == ['aaa']


def test_append_to_history_noop():
    with mock_history(initial=['aaa']) as releases:
        append_to_history('aaa')
        assert releases == ['aaa']


def test_append_to_history_repeat():
    with mock_history(initial=['aaa', 'bbb']) as releases:
        append_to_history('aaa')
        assert releases == ['aaa', 'bbb', 'aaa']


def test_rollback_history():
    with mock_history(initial=['aaa', 'bbb']) as releases:
        rollback_history()
        assert releases == ['aaa']


def test_rollback_history_to_last():
    with mock_history(initial=['aaa']) as releases:
        rollback_history()
        assert releases == []


def test_rollback_history_empty():
    with mock_history(initial=[]) as releases:
        rollback_history()
        assert releases == []


def test_rollback_history_missing():
    with mock_history(initial=None):
        # just make sure this doesn't throw
        rollback_history()
