import datetime
import logging

from gonzo.backends.aws import TIME_FORMAT
from gonzo.backends.base.instance import BaseInstance

logger = logging.getLogger(__name__)


class Instance(BaseInstance):
    running_state = 'running'
    internal_address_dns_type = 'CNAME'

    @property
    def cloud(self):
        from gonzo.backends.aws.cloud import Cloud
        return Cloud()

    @property
    def name(self):
        return self._server.tags.get('Name')

    @property
    def tags(self):
        return self._server.tags

    @property
    def region_name(self):
        return self._server.region.name

    @property
    def groups(self):
        return self._server.groups

    @property
    def availability_zone(self):
        return self._server.placement

    @property
    def instance_type(self):
        return self._server.instance_type

    @property
    def launch_time(self):
        time_str = self._server.launch_time
        return datetime.datetime.strptime(time_str, TIME_FORMAT)

    @property
    def status(self):
        return self._server.state

    def update(self):
        return self._server.update()

    def add_tag(self, key, value):
        self._server.add_tag(key, value)

    def set_name(self, name):
        self.add_tag('Name', name)

    def internal_address(self):
        return self._server.public_dns_name

    def terminate(self):
        self._server.terminate()
