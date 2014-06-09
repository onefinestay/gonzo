import types

import pytest
from mock import Mock, MagicMock, patch


from gonzo.backends.openstack.instance import Instance as OpenStackInstance
from gonzo.backends.aws.instance import Instance as AwsInstance


# default value for the address given to an instance by any cloud
SERVER_ADDRESS = '10.0.0.1'


@pytest.yield_fixture
def openstack_state():
    state = {
        'cloud': 'openstack',
        'region': 'regionname',
    }
    with patch('gonzo.config.global_state', state):
        yield


@pytest.yield_fixture
def aws_state():
    state = {
        'cloud': 'aws',
        'region': 'regionname',
    }
    with patch('gonzo.config.global_state', state):
        yield


@pytest.yield_fixture
def config():
    config = types.ModuleType('Config', 'Dummy gonzo config')
    config.CLOUDS = {
        'amazon': {
            'BACKEND': 'gonzo.backends.aws',
            'DNS_SERVICE': 'route53',
            'ORCHESTRATION_TEMPLATE_URIS': {
                'default': 'dont-want-this',
                'stackname': 'awsstack',
            }
        },
        'openstack': {
            'BACKEND': 'gonzo.backends.openstack',
            'DNS_SERVICE': 'route53',
            'DNS_ZONE': 'example.com',
            'AWS_ACCESS_KEY_ID': 'ABC',
            'AWS_SECRET_ACCESS_KEY': 'ABC',
            'ORCHESTRATION_TEMPLATE_URIS': {
                'default': 'dont-want-this',
                'stackname': 'openstack',
            }
        }
    }

    with patch('gonzo.config.get_config_module') as get_config_module:
        get_config_module.return_value = config
        yield


@pytest.yield_fixture
def mock_route53_conn():
    with patch('gonzo.backends.dns_services.route53.Route53Connection'):
        yield


@pytest.fixture
def openstack_instance():
    os_addresses = {
        'private': [{'addr': SERVER_ADDRESS}]
    }
    os_server = MagicMock()
    os_server.addresses = os_addresses
    instance = OpenStackInstance(server=os_server)
    return instance


@pytest.fixture
def aws_instance():
    aws_address = SERVER_ADDRESS
    aws_server = MagicMock()
    aws_server.public_dns_name = aws_address
    instance = AwsInstance(server=aws_server)
    return instance


@pytest.fixture
def instances(openstack_instance, aws_instance):
    return (openstack_instance, aws_instance)


@pytest.yield_fixture
def minimum_config_fixture():
    cloud = {
        'IMAGE_NAME': 'ofo',
        'PUBLIC_KEY_NAME': 'keyname',
        'DNS_ZONE': 'test_dns',
    }
    sizes = {
        'default': 'instance_type.default',
        'role-specific': 'instance_type.role_specific',
    }

    with patch('gonzo.config.get_config_module') as get_config_module:
        get_config_module.return_value = Mock(SIZES=sizes,
                                              CLOUDS={'cloudname': cloud})
        with patch('gonzo.config.global_state', {
            'cloud': 'cloudname',
            'region': 'regionname',
        }):
            yield get_config_module


@pytest.yield_fixture
def cloud_fixture():
    create_sg_target = 'gonzo.backends.create_if_not_exist_security_group'
    get_host_target = 'gonzo.backends.get_next_hostname'
    get_cloud_target = 'gonzo.backends.get_current_cloud'

    with patch(create_sg_target) as create_security_group:
        with patch(get_host_target) as get_next_hostname:
            get_next_hostname.return_value = 'prod-100'
            with patch(get_cloud_target) as get_current_cloud:
                get_current_cloud.return_value = Mock(name='cloud')
                yield (get_current_cloud,
                       get_next_hostname,
                       create_security_group)
