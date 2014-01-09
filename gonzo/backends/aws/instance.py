import datetime
from gonzo.aws.route53 import Route53
from gonzo.backends.aws import TIME_FORMAT
from gonzo.backends.base.instance import BaseInstance


class Instance(BaseInstance):
    running_state = 'running'

    @property
    def name(self):
        return self._parent.tags.get('Name')

    @property
    def tags(self):
        return self._parent.tags

    @property
    def region_name(self):
        return self._parent.region.name

    @property
    def groups(self):
        return self._parent.groups

    @property
    def availability_zone(self):
        return self._parent.placement

    @property
    def instance_type(self):
        return self._parent.instance_type

    @property
    def launch_time(self):
        time_str = self._parent.launch_time
        return datetime.datetime.strptime(time_str, TIME_FORMAT)

    @property
    def status(self):
        return self._parent.state

    def update(self):
        return self._parent.update()

    def add_tag(self, key, value):
        self._parent.add_tag(key, value)

    def set_name(self, name):
        self.add_tag('Name', name)

    def internal_address(self):
        return self._parent.public_dns_name

    def create_dns_entry(self, name=None):
        value = self.internal_address()
        if name is None:
            name = self.name
        r53 = Route53()
        r53.add_remove_record(name, "CNAME", value)

    def create_dns_entries_from_tag(self, key, delimiter=','):
        if key not in self.tags:
            return
        names = self.tags[key].split(delimiter)
        for name in names:
            self.create_dns_entry(name)

    def delete_dns_entries(self):
        r53 = Route53()
        r53.delete_dns_by_value(self.internal_address())

    def terminate(self):
        self._parent.terminate()
