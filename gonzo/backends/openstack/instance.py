import datetime

from gonzo.aws.route53 import Route53
from gonzo.backends.base.instance import BaseInstance
from gonzo.backends.openstack import OPENSTACK_AVAILABILITY_ZONE, TIME_FORMAT
from gonzo.config import config_proxy as config


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

    def create_dns_entry(self, name=None):
        ip = self.internal_address()
        if name is None:
            name = self.name
        r53 = Route53()
        r53.add_remove_record(name, "A", ip, "CREATE")

    def create_dns_entries_from_tag(self, key='cnames'):
        if key not in self.tags:
            return
        names = self.tags[key].split(',')
        for name in names:
            self.create_dns_entry(name)

    def delete_dns_entries(self):
        r53 = Route53()
        r53.delete_dns_by_value(self.internal_address())

    def terminate(self):
        self._parent.delete()
