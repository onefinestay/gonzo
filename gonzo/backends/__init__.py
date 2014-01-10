import os
from urlparse import urlparse

from jinja2 import Environment
import requests

from gonzo.aws.route53 import Route53
from gonzo.config import config_proxy as config
from gonzo.exceptions import DataError


def get_current_cloud():
    backend = config.CLOUD['BACKEND']
    cloud_module = __import__(
        "%s.cloud" % backend, globals(), locals(), ['Cloud'])
    return cloud_module.Cloud()


def get_next_hostname(env_type):
    """ Calculate the next hostname for a given environment, server_type
        returns the full hostname, including the counter, e.g.
        production-ecommerce-web-013
    """
    record_name = "-".join(["_count", env_type])
    next_count = 1
    r53 = Route53()
    try:
        count_value = r53.get_values_by_name(record_name)[0]
        next_count = int(count_value.replace('\"', '')) + 1
        r53.update_record(record_name, "TXT", "%s" % next_count)
    except:  # TODO: specify
        r53.add_remove_record(record_name, "TXT", "%s" % next_count)
    name = "%s-%03d" % (env_type, next_count)
    return name


def create_if_not_exist_security_group(group_name):
    cloud = get_current_cloud()
    if not cloud.security_group_exists(group_name):
        cloud.create_security_group(group_name)


def launch_instance(env_type, size=None,
                    user_data_uri=None, user_data_params=None,
                    security_groups=None, owner=None):
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
            username (string): username to set as owner
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

    tags = {
        'environment': environment,
        'server_type': server_type,
    }

    if owner:
        tags['owner'] = owner

    security_groups = add_default_security_groups(server_type, security_groups)
    for security_group in security_groups:
        create_if_not_exist_security_group(security_group)

    user_data = None
    user_data_uri_config_key = 'DEFAULT_USER_DATA'
    user_data_params_config_key = 'USER_DATA_PARAMS'
    user_data_uri = config.get_cloud_config(user_data_uri_config_key,
                                            override=user_data_uri)
    if user_data_uri is not None:
        user_data = get_data(name, user_data_uri, user_data_params_config_key,
                             user_data_params)

    return cloud.launch(
        name, image_name, size, zone, security_groups, key_name,
        user_data=user_data, tags=tags)


def launch_stack(stack_name, template_uri, template_params):
    """ Launch stacks """
    stack_name = get_next_hostname(stack_name)

    template_uri_config_key = 'DEFAULT_ORCHESTRATION_TEMPLATE'
    template_params_config_key = 'ORCHESTRATION_TEMPLATE_PARAMS'
    template_uri = config.get_cloud_config(template_uri_config_key,
                                           override=template_uri)
    template = get_data(stack_name, template_uri,
                        template_params_config_key, template_params)

    cloud = get_current_cloud()
    return cloud.launch_stack(stack_name, template)


def add_default_security_groups(server_type, additional_security_groups=None):
    # Set defaults
    security_groups = [server_type, 'gonzo']

    # Add argument passed groups
    if additional_security_groups is not None:
        security_groups += additional_security_groups

    # Remove Duplicates
    security_groups = list(set(security_groups))

    return security_groups


def get_data(entity_name, uri=None, config_params_key=None,
             additional_params=None):
    """ Fetch a document from uri specified by `uri` and parse as a template.
    Template parameters include cli, config and predefined dictionaries.
    Useful for building CloudFormation templates or UserData scripts.
    """
    user_data_params = build_params_dict(entity_name, config_params_key,
                                         additional_params)
    return load_data(uri, user_data_params)


def build_params_dict(entity_name, config_params_key, additional_params=None):
    """ Returns a dictionary of parameters to use when rendering CloudFormation
    templates or user data scripts from template.

    Parameter sources include gonzo defined defaults, cloud configuration and
    a comma separated key value command line argument. They get overridden in
    that order. """
    params = {
        'hostname': entity_name,
        'stackname': entity_name,
        'domain': config.CLOUD['DNS_ZONE'],
        'fqdn': "%s.%s" % (entity_name, config.CLOUD['DNS_ZONE']),
    }

    if config_params_key in config.CLOUD:
        params.update(config.CLOUD[config_params_key])

    if additional_params is not None:
        params.update(additional_params)

    return params


def load_data(uri, params=None):
    """ Attempt to fetch user data from URL or file. And render, replacing
     parameters """

    if uri is None:
        raise ValueError("Document URI cannot be None")

    try:
        urlparse(uri)
        data = fetch_from_url(uri)
    except requests.exceptions.MissingSchema:
        # Not a url. possibly a file.
        uri = os.path.expanduser(uri)
        uri = os.path.abspath(uri)

        if os.path.isabs(uri):
            try:
                data = open(uri, 'r').read()
            except IOError as err:
                err_msg = "Failed to read from file: {}".format(err)
                raise DataError(err_msg)
        else:
            # Not url nor file.
            err_msg = "Unknown UserData source: {}".format(uri)
            raise DataError(err_msg)
    except requests.exceptions.ConnectionError as err:
        err_msg = "Failed to read from URL: {}".format(err)
        raise DataError(err_msg)

    if not params:
        return data

    data_tpl = Environment().from_string(data)
    return data_tpl.render(params)


def fetch_from_url(url):
    resp = requests.get(url)
    if resp.status_code != requests.codes.ok:
        raise requests.exceptions.ConnectionError("Bad response")

    return resp.text


def configure_instance(instance):
    instance.create_dns_entry()


def terminate_stack(stack_name_or_id):
    cloud = get_current_cloud()
    return cloud.terminate_stack(stack_name_or_id)
