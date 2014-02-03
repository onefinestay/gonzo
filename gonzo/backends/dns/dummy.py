import logging
import sys

from gonzo.backends.base.dns import DNSService

logger = logging.getLogger(__name__)


class DNS(DNSService):
    """ "BlackHole" for DNS record requests.

    config usage:
        ``'DNS_SERVICE': 'dummy'``

    """
    def __init__(self):
        self._warn()

    def _warn(self):
        sys.stdout(
            'No DNS Service is configured. '
            'Host names will not be available!'
        )

    def add_remove_record(self, *args, **kwargs):
        logger.info('no DNS handler for "add_remove_record"')

    def delete_record(self, *args, **kwargs):
        logger.info('no DNS handler for "delete_record"')

    def update_record(self, *args, **kwargs):
        logger.info('no DNS handler for "update_record"')

    def get_record_by_name(self, *args, **kwargs):
        logger.info('no DNS handler for "get_record_by_name"')

    def replace_a_record(self, *args, **kwargs):
        logger.info('no DNS handler for "replace_a_record"')

    def get_record_by_value(self, *args, **kwargs):
        logger.info('no DNS handler for "get_record_by_value"')

    def get_values_by_name(self, *args, **kwargs):
        logger.info('no DNS handler for "get_values_by_name"')
        return []

    def fqdn(self, *args, **kwargs):
        logger.info('no DNS handler for "fqdn"')
