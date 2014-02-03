import datetime

from gonzo.backends import get_current_cloud
from gonzo.backends.base.instance import BaseInstance
from gonzo.backends.openstack import OPENSTACK_AVAILABILITY_ZONE, TIME_FORMAT
from gonzo.config import config_proxy as config


class Instance(BaseInstance):
    running_state = 'ACTIVE'
    internal_address_dns_type = 'A'

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

    def terminate(self):
        self._parent.delete()
