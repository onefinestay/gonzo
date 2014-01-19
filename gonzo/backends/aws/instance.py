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

    def create_dns_entry(self):
        cname = self.internal_address()
        cloud = get_current_cloud()
        dns_provider = cloud.dns
        dns_provider.add_remove_record(self.name, "CNAME", cname)

    def terminate(self):
        self._parent.terminate()
