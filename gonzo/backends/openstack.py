import datetime

from novaclient.v1_1 import client as nova_client
from novaclient.exceptions import NotFound, NoUniqueMatch

from gonzo.aws.route53 import Route53
from gonzo.backends.base import BaseInstance, BaseCloud
from gonzo.config import config_proxy as config


OPENSTACK_AVAILABILITY_ZONE = "nova"
TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


class Instance(BaseInstance):
    running_state = 'ACTIVE'

    def _refresh(self):
        self._parent = self._parent.manager.get(self._parent.id)

    @property
    def name(self):
        return self._parent.name

    @property
    def tags(self):
        return self._parent.metadata

    @property
    def region_name(self):
        return config.REGION

    @property
    def groups(self):
        # TODO: security groups
        return []

    @property
    def availability_zone(self):
        return OPENSTACK_AVAILABILITY_ZONE

    @property
    def instance_type(self):
        flavour_info = self._parent.flavor
        api = self._parent.manager.api
        flavour = api.flavors.get(flavour_info['id'])
        return flavour.name

    @property
    def launch_time(self):
        time_str = self._parent.created
        return datetime.datetime.strptime(time_str, TIME_FORMAT)

    @property
    def status(self):
        return self._parent.status

    def update(self):
        self._refresh()
        return self.status

    def add_tag(self, key, value):
        server = self._parent
        server.manager.set_meta(server, {key: value})
        self._refresh()

    def set_name(self, name):
        server = self._parent
        server.manager.update(server, name=name)
        self._refresh()

    def internal_address(self):
        addresses = self._parent.addresses
        privates = addresses['private']
        private = privates[0]
        ip = private['addr']
        return ip

    def create_dns_entry(self):
        ip = self.internal_address()
        r53 = Route53()
        r53.replace_a_record(ip, self.name)

    def terminate(self):
        self._parent.delete()


class Cloud(BaseCloud):
    instance_class = Instance

    def _list_instances(self):
        instances = self.connection.list()
        return map(self.instance_class, instances)

    def list_security_groups(self):
        return self.connection.api.security_groups.list()

    def _list_instance_types(self):
        return self.connection.api.flavors.list()

    def create_security_group(self, sg_name):
        """ Creates a security group """
        sg = self.connection.api.security_groups.create(
            sg_name, 'Rules for %s' % sg_name)
        return sg

    def get_image_by_name(self, name):
        """ Find image by name """
        try:
            return self.connection.api.images.find(name=name)
        except (NotFound, NoUniqueMatch):
            # in case we want to do/throw something else later
            raise

    def get_available_azs(self):
        """ Return a list of AZs - as single characters, no region info"""
        return [OPENSTACK_AVAILABILITY_ZONE]

    _connection = None

    @property
    def connection(self):
        if self._connection is None:

            client = nova_client.Client(
                config.CLOUD['USERNAME'],
                config.CLOUD['PASSWORD'],
                config.CLOUD['TENANT_NAME'],
                config.CLOUD['AUTH_URL'],
                service_type="compute")
            self._connection = client.servers
        return self._connection

    def _get_instance_type(self, name):
        flavours = self._list_instance_types()
        for flavour in flavours:
            if flavour.name == name:
                return flavour
        raise KeyError("%s not found in instance type list" % name)

    def next_az(self, server_type):
        """ Returns the next AZ to use, keeping the use of AZs balanced """
        return OPENSTACK_AVAILABILITY_ZONE

    def launch(
            self, name, image_name, instance_type, zone,
            security_groups, key_name, tags=None):
        image = self.get_image_by_name(image_name)
        flavour = self._get_instance_type(instance_type)
        userdata = config.CLOUD.get('USERDATA')

        logger.info('userdata: {}'.format(userdata))

        raw_instance = self.connection.create(
            name, image.id, userdata=userdata,
            flavor=flavour.id, availability_zone=zone,
            security_groups=security_groups, key_name=key_name)

        instance = self.instance_class(raw_instance)

        tags = tags or {}

        for tag, value in tags.items():
            instance.add_tag(tag, value)

        return instance
