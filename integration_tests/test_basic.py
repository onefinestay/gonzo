from gonzo.tasks.release import activate, list_releases, push


def test_basic(container, test_repo):
    push()
    activate()
    test_repo.add_commit()
    push()
    activate()
    test_repo.add_commit()
    push()
    history = list_releases()
    assert len(history) == 2
