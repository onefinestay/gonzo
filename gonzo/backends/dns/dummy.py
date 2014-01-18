import logging
import sys

from gonzo.backends.dns import DNSService, AVAILABLE_SERVICES
from gonzo.backends.dns import exceptions

logger = logging.getLogger(__name__)


class DNS(DNSService):
    def __init__(self):
        self.warn()

    def warn(self):
        sys.stdout(
            '\nNo DNS Service is configured. '
            'Host names will not be available!\n'
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
        # TOTHINK: not sure what to do here.
        # i don't like the auto-generation of names in the first place.
        # TODO: look at why callers of this assume things of the list values
        return [-1]

    def fqdn(self, *args, **kwargs):
        logger.info('no DNS handler for "fqdn"')
