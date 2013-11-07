from gonzo.backends.base import add_default_security_groups


def test_default_security_groups():
    groups = add_default_security_groups('server-type', ['gonzo', 'test'])

    # Test for default groups and no duplicates
    assert groups.count('gonzo') == 1
    assert sorted(groups) == ['gonzo', 'server-type', 'test']
