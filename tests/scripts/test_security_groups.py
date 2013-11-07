from mock import patch

from gonzo.backends.base import get_security_groups


@patch('gonzo.backends.base.create_if_not_exist_security_group')
def test_security_groups(create):
    security_groups = get_security_groups(server_type='server-type',
                                          security_groups_arg="gonzo,test")

    # Test for default groups and no duplicates
    assert security_groups.count('gonzo') == 1
    assert sorted(security_groups) == ['gonzo', 'server-type', 'test']
