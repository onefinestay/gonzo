import datetime

from gonzo.backends.base.instance import BaseInstance
from gonzo.backends.openstack import OPENSTACK_AVAILABILITY_ZONE, TIME_FORMAT
from gonzo.config import config_proxy as config


class Instance(BaseInstance):
    """An Openstack server
    """

    running_state = 'ACTIVE'
    internal_address_dns_type = 'A'

    def __init__(self, server):
        self._server = server

    def _refresh(self):
        self._server = self._server.manager.get(self._server.id)

    @property
    def name(self):
        return self._server.name

    @property
    def tags(self):
        return self._server.metadata

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
        flavour_info = self._server.flavor
        api = self._server.manager.api
        flavour = api.flavors.get(flavour_info['id'])
        return flavour.name

    @property
    def launch_time(self):
        time_str = self._server.created
        return datetime.datetime.strptime(time_str, TIME_FORMAT)

    @property
    def status(self):
        return self._server.status

    def update(self):
        self._refresh()
        return self.status

    def add_tag(self, key, value):
        server = self._server
        server.manager.set_meta(server, {key: value})
        self._refresh()

    def set_name(self, name):
        server = self._server
        server.manager.update(server, name=name)
        self._refresh()

    def internal_address(self):
        """Return the internal IP given to this instance
        from the Cloud's pool.

        """
        addresses = self._server.addresses
        privates = addresses['private']
        private = privates[0]
        ip = private['addr']
        return ip

    def terminate(self):
        self._server.delete()
