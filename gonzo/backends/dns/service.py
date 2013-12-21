import imp
import os
from abc import ABCMeta, abstractmethod, abstractproperty

from gonzo.config import config_proxy as config

AVAILABLE_SERVICES = ['Route53']


class DNSService(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def add_remove_record(self):
        """ Creates a new record in the zone """

    @abstractmethod
    def update_record(self):
        """ Updates a record in the zone """

    @abstractmethod
    def get_record_by_name(self, env_type):
        """ Derives a host name """

    @abstractmethod
    def replace_a_record(self, ipaddress, name):
        """ replace ip address on A record """

    @abstractmethod
    def get_record_by_value(self, value):
        """ Returns the record with value """

    @abstractmethod
    def get_values_by_name(self, name):
        """ Returns the values all records by name """

    @abstractmethod
    def fqdn(self, name):
        """ Utility to turn a hostname into a FQDN """

    @abstractmethod
    def clean_value(self, type, value):
        """ TXT records, and probably others need values to be quoted"""


def get_dns_service():
    service_name = config.DNS
    path_to_services = os.path.dirname(__file__)

    try:
        module = imp.find_module(
            service_name, [path_to_services])
    except ImportError:
        raise ConfigurationError(
            'DNS option {} does not exist.'.format(service_name)
        )

    dns_module = imp.load_module(service_name, *module)
    dns_service = dns_module.DNS()

    return dns_service
