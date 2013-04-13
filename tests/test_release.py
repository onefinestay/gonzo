from mock import patch

from gonzo.tasks.release import get_adjacent_release, NEXT, PREVIOUS


@patch('gonzo.tasks.release.get_releases')
def test_get_adjacent_release(get_releases):
    releases = [
        'aaa',
        'bbb',
        'ccc',
        'ddd',
    ]

    get_releases.return_value = releases

    assert get_adjacent_release('ccc') == 'ddd'
    assert get_adjacent_release('ccc', NEXT) == 'ddd'
    assert get_adjacent_release('ccc', PREVIOUS) == 'bbb'

    assert get_adjacent_release(None) == 'ddd'
    assert get_adjacent_release(None, NEXT) == 'ddd'
    assert get_adjacent_release(None, PREVIOUS) == 'aaa'

    assert get_adjacent_release('aaa', PREVIOUS) is None
    assert get_adjacent_release('ddd', NEXT) is None

    assert get_adjacent_release('xxx') is None
    assert get_adjacent_release('xxx', NEXT) is None
    assert get_adjacent_release('xxx', PREVIOUS) is None


@patch('gonzo.tasks.release.get_releases')
def test_get_adjacent_release_ho_history(get_releases):
    releases = []

    get_releases.return_value = releases

    assert get_adjacent_release(None) is None
    assert get_adjacent_release(None, NEXT) is None
    assert get_adjacent_release(None, PREVIOUS) is None

    assert get_adjacent_release('xxx') is None
    assert get_adjacent_release('xxx', NEXT) is None
    assert get_adjacent_release('xxx', PREVIOUS) is None
