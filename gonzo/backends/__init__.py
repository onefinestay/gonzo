import json
import logging

from gonzo import exceptions

from gonzo.config import config_proxy as config
from gonzo.helpers.document_loader import get_parsed_document

logger = logging.getLogger(__name__)


def get_current_cloud():
    backend = config.CLOUD['BACKEND']
    cloud_module = __import__(
        "%s.cloud" % backend, globals(), locals(), ['Cloud'])
    return cloud_module.Cloud()


def get_next_hostname(env_type):
    """ Calculate the next hostname for a given environment, server_type
        returns the full hostname, including the counter, e.g.
        production-ecommerce-web-013

        .. note::

            Gonzo's host name protocol follows the pattern:
            <project_name>-<environment_name>-<version_number>

            It's essential that the version number is unique between the cloud's
            past, present and future servers, so next values are held on DNS TXT
            records and then calculated from.

    """
    record_name = "-".join(["_count", env_type])
    cloud = get_current_cloud()
    dns_service = cloud.dns
    next_count = 1

    try:
        values = dns_service.get_values_by_name(record_name)
    except exceptions.DNSRecordNotFoundError:
        dns_service.add_remove_record(record_name, "TXT", "1")
    else:

        try:
            count_value = values[0]
            next_count = int(count_value.replace('\"', '')) + 1
        except (IndexError, ValueError):
            pass

        try:
            dns_service.update_record(record_name, "TXT", "%s" % next_count)
        except exceptions.DNSRecordUpdateError:
            logger.exception(
                'Failed updating DNS record: %s', record_name)
            raise

    name = "%s-%03d" % (env_type, next_count)
    logger.debug('next host name is "{}"'.format(name))
    return name


def launch_instance(env_type, size=None,
                    user_data_uri=None, user_data_params=None,
                    security_groups=None, extra_tags=None,
                    image_name=None, owner=None):
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

    image_name = config.get_cloud_config_value('IMAGE_NAME',
                                               override=image_name)

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


def generate_stack_template(stack_type, stack_name,
                            template_uri, template_params,
                            owner=None):
    template_uri = config.get_namespaced_cloud_config_value(
        'ORCHESTRATION_TEMPLATE_URIS', stack_type, override=template_uri)
    if template_uri is None:
        raise ValueError('A template must be specified by argument or '
                         'in config')

    template = get_parsed_document(
        stack_name, template_uri,
        'ORCHESTRATION_TEMPLATE_PARAMS', template_params
    )

    # Parse as json for validation and for injecting gonzo defaults
    template_dict = json.loads(template)

    if owner:
        template_dict = insert_stack_owner_output(template_dict, owner)

    return json.dumps(template_dict)


def insert_stack_owner_output(template_dict, owner):
    """ Adds a stack output to a template with key "owner" """
    template_outputs = template_dict.get('Outputs', {})
    template_outputs['owner'] = {
        'Value': owner,
        'Description': "This stack's launcher (Managed by Gonzo)"
    }
    template_dict.update({'Outputs': template_outputs})

    return template_dict


def launch_stack(stack_name, template_uri, template_params, owner=None):
    """ Launch stacks """
    import pdb
    pdb.set_trace()
    unique_stack_name = get_next_hostname(stack_name)

    template = generate_stack_template(stack_name, unique_stack_name,
                                       template_uri, template_params,
                                       owner)

    cloud = get_current_cloud()
    return cloud.launch_stack(unique_stack_name, template)


def terminate_stack(stack_name_or_id):
    cloud = get_current_cloud()
    return cloud.terminate_stack(stack_name_or_id)
