import imp
import logging
import os

from gonzo import exceptions
from gonzo.config import config_proxy as config
from gonzo.helpers.document_loader import get_parsed_document

logger = logging.getLogger(__name__)


def get_current_cloud():
    backend = config.CLOUD['BACKEND']
    cloud_module = __import__(
        "%s.cloud" % backend, globals(), locals(), ['Cloud'])
    return cloud_module.Cloud()


def get_dns_service():
    service_name = config.DNS.lower()
    path_to_services = os.path.join(os.path.dirname(__file__), 'dns_services')

    try:
        module = imp.find_module(
            service_name, [path_to_services])
    except ImportError:
        raise exceptions.ConfigurationError(
            'DNS option {dns_provider} does not exist. '.format(
                dns_provider=service_name,
            )
        )

    dns_module = imp.load_module(service_name, *module)
    dns_service = dns_module.DNS()

    return dns_service


def get_next_hostname(env_type):
    """ Calculate the next hostname for a given environment, server_type
        returns the full hostname, including the counter, e.g.
        production-ecommerce-web-013
    """
    record_name = "-".join(["_count", env_type])
    cloud = get_current_cloud()
    dns_service = cloud.dns

    try:
        values = dns_service.get_values_by_name(record_name)
    except exceptions.DNSRecordNotFoundError:
        dns_service.add_remove_record(record_name, "TXT", "1")
    else:

        try:
            count_value = values[0]
            next_count = int(count_value.replace('\"', '')) + 1
        except (IndexError, ValueError):
            next_count = 1

        try:
            dns_service.update_record(record_name, "TXT", "%s" % next_count)
        except exceptions.DNSRecordUpdateError as exc:
            logger.exception(
                'Failed updating DNS record %s: %s', record_name, exc)
            raise

    name = "%s-%03d" % (env_type, next_count)
    logger.debug('next host name is "{}"'.format(name))
    return name


def launch_instance(env_type, size=None,
                    user_data_uri=None, user_data_params=None,
                    security_groups=None, extra_tags=None, owner=None):
    """ Launch instances

        Arguments:
            env_type (string): environment-server_type
            size (string): size of the instance to launch.
            user_data_uri (string): File path or URL for user data script.
                If None, Config value will be used.
            user_data_params (dict): Dictionary or parameters to supplement
                the defaults when generating user-data.
            security_groups (list): List of security groups to create (if
                necessary) and supplement the defaults.
            owner (string): username to set as owner
    """

    cloud = get_current_cloud()
    environment, server_type = env_type.split("-", 1)

    name = get_next_hostname(env_type)

    image_name = config.CLOUD['IMAGE_NAME']

    if size is None:
        sizes = config.SIZES
        default_size = sizes['default']
        size = sizes.get(server_type, default_size)

    zone = cloud.next_az(server_type)

    key_name = config.CLOUD['PUBLIC_KEY_NAME']

    tags = extra_tags or {}
    tags.update({
        'environment': environment,
        'server_type': server_type,
    })

    if owner:
        tags['owner'] = owner

    security_groups = add_default_security_groups(server_type, security_groups)
    for security_group in security_groups:
        create_if_not_exist_security_group(security_group)

    user_data = None
    user_data_uri = config.get_cloud_config_value('DEFAULT_USER_DATA',
                                                  override=user_data_uri)
    if user_data_uri is not None:
        user_data = get_parsed_document(name, user_data_uri,
                                        'USER_DATA_PARAMS', user_data_params)

    return cloud.launch_instance(
        name, image_name, size, zone, security_groups, key_name,
        user_data=user_data, tags=tags)


def add_default_security_groups(server_type, additional_security_groups=None):
    # Set defaults
    security_groups = [server_type, 'gonzo']

    # Add argument passed groups
    if additional_security_groups is not None:
        security_groups += additional_security_groups

    # Remove Duplicates
    security_groups = list(set(security_groups))

    return security_groups


def create_if_not_exist_security_group(group_name):
    cloud = get_current_cloud()
    if not cloud.security_group_exists(group_name):
        cloud.create_security_group(group_name)


def configure_instance(instance):
    instance.create_dns_entry()


def launch_stack(stack_name, template_uri, template_params):
    """ Launch stacks """

    unique_stack_name = get_next_hostname(stack_name)

    template_uri = config.get_namespaced_cloud_config_value(
        'ORCHESTRATION_TEMPLATE_URIS', stack_name, override=template_uri)
    if template_uri is None:
        raise ValueError('A template must be specified by argument or '
                         'in config')

    template = get_parsed_document(unique_stack_name, template_uri,
                                   'ORCHESTRATION_TEMPLATE_PARAMS',
                                   template_params)

    cloud = get_current_cloud()
    return cloud.launch_stack(unique_stack_name, template)


def terminate_stack(stack_name_or_id):
    cloud = get_current_cloud()
    return cloud.terminate_stack(stack_name_or_id)
