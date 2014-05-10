import logging
import sys

from gonzo.backends.base.dns import DNSService

logger = logging.getLogger(__name__)


class DummyDNS(DNSService):
    """ "BlackHole" for DNS record requests.

    config usage:
        ``'DNS_SERVICE': 'dummy'``

    """
    name = 'dummy'

    def _warn(self, handler_name):
        sys.stdout.write(
            'No DNS handler is configured for "{}"\n'.format(handler_name)
        )

    def add_remove_record(
            self, name, type, value, action="CREATE", is_qualified=False):
        self._warn("add_remove_record")

    def update_record(self, name, type, new_value, old_value=None):
        self._warn("update_record")

    def get_record_by_name(self, name):
        self._warn("get_record_by_name")

    def replace_a_record(self, ipaddress, name):
        self._warn("replace_a_record")

    def get_values_by_name(self, name):
        self._warn("get_values_by_name")
        return []

    def fqdn(self, name):
        self._warn("fqdn")

    def delete_dns_by_value(self, get_values_by_name):
        self._warn("delete_dns_by_value")
