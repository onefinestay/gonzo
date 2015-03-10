import pytest
from mock import patch, Mock

from gonzo.clouds.compute import Openstack
from gonzo.scripts import list_, launch
from gonzo.scripts.base import get_parser


@pytest.yield_fixture
def fake_dns():
    with patch("gonzo.clouds.dns.get_dns_driver") as driver:
        yield driver


@pytest.yield_fixture(autouse=True)
def fake_get_config(request):
    with patch('gonzo.config.get_config_module') as get_config_module:
        endpoint = request.config.getoption("--devstack-endpoint")
        if endpoint is None:
            pytest.skip("No endpoint specified")
        get_config_module.return_value = Mock(
            SIZES={
                'default': 'm1.nano',
            },
            CLOUDS={
                'cloudname': {
                    'BACKEND': 'openstack',
                    'TENANT_NAME': 'admin',
                    'USERNAME': 'admin',
                    'PASSWORD': 'password',
                    'AUTH_URL': endpoint,
                    'AWS_ACCESS_KEY_ID': None,
                    'AWS_SECRET_ACCESS_KEY': None,
                    'DNS_ZONE': "example.com",
                    'DNS_TYPE': 'A',
                },
            }
        )
        with patch('gonzo.config.global_state', {
            'cloud': 'cloudname',
            'region': 'RegionOne',
        }):
                    yield get_config_module


def test_end_to_end(capsys, fake_dns, fake_get_config):

    # starts out blank
    parser = get_parser()
    args = parser.parse_args(["list"])
    list_.main(args)
    out, err = capsys.readouterr()
    assert not err
    non_blank_lines = [line for line in out.splitlines() if line.strip()]
    assert len(non_blank_lines) == 1
    printed_headers = non_blank_lines[0]
    assert printed_headers.split() == list_.headers

    openstack = Openstack(fake_get_config().CLOUDS['cloudname'],region=None)
    image_list = openstack.compute_session.list_images()
    image_map = {image.name: image.id for image in image_list}
    image_id = image_map['cirros-0.3.2-x86_64-uec']

    # launch an instance
    args = parser.parse_args(["launch", "test-launch", "--image-id={}".format(image_id)])
    launch.main(args)