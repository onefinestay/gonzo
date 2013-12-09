from urlparse import urlparse
import os
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


def launch_instance(env_type, user_data=None, user_data_params=None,
                    security_groups=None, username=None):
    """ Launch instances

        Arguments:
            env_type (string): environment-server_type
            user_data (string): File path or URL for user data script. If None,
                Config value will be used.
            user_data_params (dict): Dictionary or parameters to supplement
                the defaults when generating user-data.
            security_groups (list): List of security groups to create (if
                necessary) and supplement the defaults.

        Keyword arguments:
            username (string): username to set as owner
            wait (bool): don't return until instance is running.
                (default: True)
    """

    cloud = get_current_cloud()
    environment, server_type = env_type.split("-", 1)

    name = get_next_hostname(env_type)

    image_name = config.CLOUD['IMAGE_NAME']

    sizes = config.SIZES
    default_size = sizes['default']
    instance_type = sizes.get(environment, default_size)

    zone = cloud.next_az(server_type)

    key_name = config.CLOUD['PUBLIC_KEY_NAME']

    tags = {
        'environment': environment,
        'server_type': server_type,
    }

    if username:
        tags['owner'] = username

    security_groups = add_default_security_groups(server_type, security_groups)
    for security_group in security_groups:
        create_if_not_exist_security_group(security_group)

    user_data = get_data(name, 'DEFAULT_USER_DATA', 'USER_DATA_PARAMS',
                         user_data, user_data_params)

    return cloud.launch(
        name, image_name, instance_type, zone, security_groups, key_name,
        user_data=user_data, tags=tags)


def launch_stack(stack_name, template_location, template_params):
    """ Launch stacks """
    unique_name = get_next_hostname(stack_name)
    template = get_data(unique_name, 'DEFAULT_ORCHESTRATION_TEMPLATE',
                        'ORCHESTRATION_TEMPLATE_PARAMS',
                        template_location, template_params)

    cloud = get_current_cloud()
    return cloud.launch_stack(unique_name, template)


def add_default_security_groups(server_type, additional_security_groups=None):
    # Set defaults
    security_groups = [server_type, 'gonzo']

    # Add argument passed groups
    if additional_security_groups is not None:
        security_groups += additional_security_groups

    # Remove Duplicates
    security_groups = list(set(security_groups))

    return security_groups


def get_data(entity_name, config_uri_key, config_params_key, uri=None,
             additional_params=None):
    """ Returns a document body (as string) with a parsed template as contents.
     If specified, the template is fetched from uri (file or url), and are then
     parametrised by a built in library, extended by config and cli provided
     dicts.
    """
    user_data_params = build_params_dict(entity_name, config_params_key,
                                         additional_params)
    return load_data(user_data_params, config_uri_key, uri)


def build_params_dict(entity_name, config_params_key, additional_params=None):
    """ Returns a dictionary of parameters to use when rendering user data
     scripts from template.

     Parameter sources include gonzo defined defaults, cloud configuration and
     a comma separated key value command line argument. They are also
     overridden in that order. """
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


def load_data(params, config_uri_key, uri=None):
    """ Attempt to fetch user data from URL or file. And render, replacing
     parameters """

    if uri is None:
        # Look for a default in cloud config
        if config_uri_key in config.CLOUD:
            uri = config.CLOUD[config_uri_key]
        else:
            return None

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
