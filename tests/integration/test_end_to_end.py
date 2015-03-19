import pytest
from mock import patch, Mock
import time

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


@pytest.yield_fixture
def openstack_session(fake_get_config):
    openstack = Openstack(fake_get_config().CLOUDS['cloudname'], region=None)
    instance_list = openstack.compute_session.list_nodes()

    print "deleting instances"
    for instance in instance_list:
        openstack.compute_session.destroy_node(instance)

    time.sleep(10)  # wait for instance to be deleted

    print "deleting security groups"
    sec_groups = openstack.compute_session.ex_list_security_groups()
    for sec_group in sec_groups[1:]:  # Skip default group
        openstack.compute_session.ex_delete_security_group(sec_group)
    yield openstack


def test_end_to_end(capsys, fake_dns, fake_get_config, openstack_session):
    # list instances - should be blank
    parser = get_parser()
    args = parser.parse_args(["list"])
    list_.main(args)
    out, err = capsys.readouterr()
    assert not err
    non_blank_lines = [line for line in out.splitlines() if line.strip()]
    assert len(non_blank_lines) == 1
    printed_headers = non_blank_lines[0]
    assert printed_headers.split() == list_.headers

    image_list = openstack_session.compute_session.list_images()
    image_map = {image.name: image.id for image in image_list}
    image_id = image_map['cirros-0.3.2-x86_64-uec']

    # launch an instance
    instance_name = ["test", "launch", "instance"]
    args = parser.parse_args(["launch", "-".join(
        instance_name), "--image-id={}".format(image_id)]
    )
    launch.launch(args)
    full_instance_name = "{}-001".format("-".join(instance_name))
    instance = openstack_session.get_instance_by_name(full_instance_name)

    # check instance data
    assert instance.name == full_instance_name
    assert instance.extra['gonzo_size'] == fake_get_config().SIZES['default']
    assert instance.extra['gonzo_tags']['environment'] == instance_name[0]
    assert instance.extra['gonzo_tags']['server_type'] == ("-").join(
        instance_name[-2:]
    )

    # check security groups created
    assert openstack_session.get_security_group("launch-instance")
    assert openstack_session.get_security_group("gonzo")

    # list instances - should return 1 instance
    capsys.readouterr()  # reset stdout
    list_.main(args)
    out, err = capsys.readouterr()
    non_blank_lines = [line for line in out.splitlines() if line.strip()]
    assert len(non_blank_lines) == 2  # includes headers
