from abc import ABCMeta, abstractmethod, abstractproperty


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
    def delete_dns_entries(self):
        """ Delete all DNS records for an instance """
