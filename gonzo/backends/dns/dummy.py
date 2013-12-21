import logging
import inspect

from gonzo.backends.dns import DNSService, AVAILABLE_SERVICES


class DNS(DNSService):
    def __init__(self):
        # impose console logging,
        # as assumed to be in a private or dev environment.
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        logger = logging.getLogger(__name__)
        logger.addHandler(ch)

        self.logger = logger
        self.logger.warning(
            'No DNS Service is configured. '
            'Host names will not be available. '
            'Supported services are: {}, '
            'which you can set "DNS_SERVICE" to '
            'in your config.py.'.format(
                ', '.join(AVAILABLE_SERVICES))

        )

    def add_remove_record(self, *args, **kwargs):
        self.logger.info('dummied: %s', inspect.stack()[0][3])

    def delete_record(self, *args, **kwargs):
        self.logger.info('dummied: %s', inspect.stack()[0][3])

    def update_record(self, *args, **kwargs):
        self.logger.info('dummied: %s', inspect.stack()[0][3])

    def get_record_by_name(self, *args, **kwargs):
        self.logger.info('dummied: %s', inspect.stack()[0][3])

    def replace_a_record(self, *args, **kwargs):
        self.logger.info('dummied: %s', inspect.stack()[0][3])

    def get_record_by_value(self, *args, **kwargs):
        self.logger.info('dummied: %s', inspect.stack()[0][3])

    def get_values_by_name(self, *args, **kwargs):
        self.logger.info('dummied: %s', inspect.stack()[0][3])

    def fqdn(self, *args, **kwargs):
        self.logger.info('dummied: %s', inspect.stack()[0][3])

    def clean_value(self, *args, **kwargs):
        self.logger.info('dummied: %s', inspect.stack()[0][3])
