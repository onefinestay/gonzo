from abc import abstractmethod, abstractproperty
from os.path import expanduser
from urlparse import urlparse

import os

from jinja2 import Environment
import requests
import sys

from gonzo.aws.route53 import Route53
from gonzo.backends import get_current_cloud
from gonzo.config import config_proxy as config


# For initial connection after instance creation.
MAX_RETRIES = 10


class BaseInstance(object):
    """ Wrapper for cloud instances

        Interrogate these for name, tags and other properties
    """
    running_state = abstractproperty

    def __init__(self, parent):
        self._parent = parent

    def __repr__(self):
        return "<%s.%s %s>" % (
            self.__class__.__module__, self.__class__.__name__, self.name)

    @property
    def id(self):
        return self._parent.id

    @abstractproperty
    def name(self):
        """ Instance name """
        pass

    @abstractproperty
    def tags(self):
        """ Instance tags """
        pass

    @abstractproperty
    def region_name(self):
        pass

    @abstractproperty
    def groups(self):
        pass

    @abstractproperty
    def availability_zone(self):
        pass

    @abstractproperty
    def instance_type(self):
        pass

    @abstractproperty
    def launch_time(self):
        pass

    @abstractproperty
    def status(self):
        pass

    def is_running(self):
        return self.status == self.running_state

    # TODO: just have a dict-like `tags` attribute?

    @abstractmethod
    def add_tag(self, key, value):
        pass

    @abstractmethod
    def set_name(self, name):
        pass

    def has_tags(self, **tags):
        """ Utility; returns True if the given instance has the specified tags
            set as per the keyword args."""
        for key, value in tags.items():
            try:
                if self.tags[key] != value:
                    return False
            except KeyError:
                return False

        return True

    @abstractmethod
    def internal_address(self):
        pass

    @abstractmethod
    def create_dns_entry(self):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def terminate(self):
        pass


class BaseCloud(object):
    """ Wrapper for cloud providers

        provides methods for listing, adding or deleting instances,
        as well as for interacting with security groups, roles and
        availability zones
    """

    instance_class = abstractproperty

    @abstractproperty
    def connection(self):
        pass

    @abstractmethod
    def _list_instances(self):
        pass

    def list_instances(self, only_running=True):
        """ Return a list of all (running) instances """
        instances = self._list_instances()
        if only_running:
            instances = [i for i in instances if i.status == i.running_state]

        return instances

    @abstractmethod
    def list_security_groups(self):
        pass

    def get_security_group(self, name):
        """ Return the named security group """
        groups = self.list_security_groups()
        for group in groups:
            if group.name == name:
                return group

        raise Exception("Invalid security group: %s " % name)

    def security_group_exists(self, name):
        """ Returns true if the security group exists, otherwise false"""
        groups = self.list_security_groups()
        for group in groups:
            if name == group.name:
                return True

        return False

    @abstractmethod
    def create_security_group(self, sg_name):
        """ Creates a security group """
        pass

    @abstractmethod
    def get_image_by_name(self, name):
        """ Find image by name """

    def get_instance_by_name(self, name):
        """ Return instance having given name """
        instances = self.list_instances()
        instance = [i for i in instances if i.name == name]
        if not instance:
            raise KeyError("No instances returned with name %s" % name)
        return instance[0]

    def get_instance_by_tags(self, **tags):
        """ Return list of all instances having tags assigned as in
            keyword args.
        """
        instances = self.list_instances()
        relevant_instances = [
            i for i in instances if i.has_tags(**tags)]
        relevant_instances.sort(key=lambda i: i.name)
        return relevant_instances

    def get_instance_by_id(self, instid):
        """ Return instance having given ID """
        instance = [i for i in self.list_instances() if i.id == instid]
        if not instance:
            raise KeyError("No instances returned with ID %s" % instid)

        return instance[0]

    @abstractmethod
    def get_available_azs(self):
        """ Return a list of AZs - as single characters, no region info"""
        pass

    @abstractmethod
    def get_instance_by_dns(self, address):
        pass

    def get_instance(self, name_or_id):
        """ Return instance having name, ID or DNS name as given
            to name_or_id.
        """
        try:
            return self.get_instance_by_name(name_or_id)
        except KeyError:
            pass

        try:
            return self.get_instance_by_dns(name_or_id)
        except KeyError:
            pass

        return self.get_instance_by_id(name_or_id)

    @abstractmethod
    def next_az(self, server_type):
        """ Returns the next AZ to use, keeping the use of AZs balanced """
        pass

    @abstractmethod
    def launch(
            self, name, image_name, instance_type, zone, security_groups,
            key_name, user_data=None, tags=None):
        """ Launch an instance """
        pass


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

    if security_groups is not None:
        for security_group in security_groups:
            create_if_not_exist_security_group(security_group)

    key_name = config.CLOUD['PUBLIC_KEY_NAME']

    tags = {
        'environment': environment,
        'server_type': server_type,
    }

    if username:
        tags['owner'] = username

    user_data = get_user_data(name, user_data, user_data_params)

    return cloud.launch(
        name, image_name, instance_type, zone, security_groups, key_name,
        user_data=user_data, tags=tags)


def get_user_data(hostname, arg_ud_uri=None, arg_ud_params=None):
    user_data_params = build_user_data_params_dict(hostname, arg_ud_params)

    try:
        return load_user_data(user_data_params, arg_ud_uri)
    except requests.exceptions.ConnectionError as err:
        abort("Failed to connect to user-data source\n%s" % err.strerror)
    except IOError as err:
        abort("Failed to read file\n%s" % err.strerror)


def build_user_data_params_dict(hostname, arg_params=None):
    """ Returns a dictionary of parameters to use when rendering user data
     scripts from template.

     Parameter sources include gonzo defined defaults, cloud configuration and
     a comma separated key value command line argument. They are also
     overridden in that order. """
    params = {'hostname': hostname,
              'domain': config.CLOUD['DNS_ZONE'],
              'fqdn': "%s.%s" % (hostname, config.CLOUD['DNS_ZONE'])}

    if 'USER_DATA_PARAMS' in config.CLOUD:
        params.update(config.CLOUD['USER_DATA_PARAMS'])

    if arg_params is not None:
        # Parse argument supplied user data params to dictionary
        arg_params = dict(kv.split("=") for kv in arg_params.split(","))
        params.update(arg_params)

    return params


def load_user_data(user_data_params, user_data_uri=None):
    """ Attempt to fetch user data from URL or file. And render, replacing
     parameters """

    if user_data_uri is None:
        # Look for a default in cloud config
        if 'DEFAULT_USER_DATA' in config.CLOUD:
            user_data_uri = config.CLOUD['DEFAULT_USER_DATA']
        else:
            return None

    try:
        urlparse(user_data_uri)

        resp = requests.get(user_data_uri)
        if resp.status_code != requests.codes.ok:
            raise requests.exceptions.ConnectionError("Bad response")

        user_data = resp.text
    except requests.exceptions.MissingSchema:
        # Not a url. possibly a file.
        user_data_uri = expanduser(user_data_uri)
        user_data_uri = os.path.abspath(user_data_uri)
        if os.path.isabs(user_data_uri):
            user_data = file(user_data_uri, 'r').read()
        else:
            return None

    user_data_tpl = Environment().from_string(user_data)
    return user_data_tpl.render(user_data_params)


def configure_instance(instance):
    instance.create_dns_entry()


def abort(message=None):
    if message is not None:
        print >> sys.stderr, message

    sys.exit(1)
