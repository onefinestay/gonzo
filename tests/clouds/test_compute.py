from mock import Mock, patch
import pytest

from gonzo.clouds.compute import Cloud


def make_fake_instance(**kwargs):
    instance = Mock(extra={})
    for key, value in kwargs.items():
        instance.extra[key] = value
    return instance


class MockCloud(Cloud):
    def __init__(self, zones, instances):
        self.zones = zones
        self.instances = instances

    def list_availability_zones(self):
        zone_list = []
        for zone in self.zones:
            mock = Mock()
            mock.name = zone
            zone_list.append(mock)
        return zone_list

    def list_instances_by_type(self, instance_type):
        return self.instances


def test_get_next_az_foo():
    cloud = MockCloud(
        zones=['a'], instances=[make_fake_instance(gonzo_az='x')]
    )
    az = cloud.get_next_az(server_type=["foo", "bar"])
    assert az.name == 'a'


def test_get_next_az_unknown_zone():
    pass


@pytest.mark.parametrize(
    ('zones', 'instance_zones', 'expected'),
    [
        (['a', 'b'], [], 'a'),
        (['a', 'b'], ['a'], 'b'),
        (['a', 'b'], ['b'], 'a'),
        (['a', 'b'], ['a', 'b'], 'a'),
        (['a', 'b'], ['a', 'a', 'b'], 'a'),  # always uses "newest"
    ])
def test_get_next_az(zones, instance_zones, expected):
    instances = [
        make_fake_instance(gonzo_az=zone) for zone in instance_zones
    ]

    cloud = MockCloud(zones=zones, instances=instances)
    az = cloud.get_next_az(server_type=["foo", "bar"])
    assert az.name == expected


def test_missing_backend():
    with pytest.raises(LookupError) as exc_info:
        Cloud.from_config({}, "region")
    assert 'No backend specified' in str(exc_info.value)
