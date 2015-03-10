from libcloud.dns.providers import get_driver as get_dns_driver
from libcloud.dns.types import Provider as DNSProvider
from libcloud.dns.types import RecordType


class DNS(object):

    def __init__(self, aws_access_id, aws_secret_key):
        R53Drver = get_dns_driver(DNSProvider.ROUTE53)
        #import ipdb; ipdb.set_trace()
        self.dns_session = R53Drver(aws_access_id, aws_secret_key)

    def get_next_host(self, environment, server_type, zone):
        record_type = RecordType.TXT
        record_name = "_count-%s-%s" % (environment, server_type)
        try:  # Try to update record first
            dns_record = self.get_dns_record(zone=self.get_zone(zone),
                                             record_name=record_name)

            next_count = int(dns_record.data.strip('"')) + 1
            print "Updating DNS Counter..."
            print self.dns_session.update_record(record=dns_record,
                                                 name=record_name,
                                                 type=record_type,
                                                 data='"{}"'.format(str(
                                                     next_count)))
        except Exception:
            print "Creating New DNS Counter..."
            print self.dns_session.create_record(zone=self.get_zone(zone),
                                                 name=record_name,
                                                 type=record_type, data='"1"')

    def get_zone(self, zone_name):
        for zone in self.dns_session.iterate_zones():
            if zone_name == zone.domain[:-1]:
                return zone

    def get_dns_record(self, record_name, zone):
        for dns_record in self.dns_session.iterate_records(
                self.get_zone(zone)):
            if record_name == dns_record.name:
                print "Matched"
                return dns_record
        # TODO Raise exception on failure

    def get_record_type(self, record_name):
        pass

    def create_dns_record(self, name, value, record_type, zone_name):
        return self.dns_session.create_record(
            name=name,
            zone=self.get_zone(zone_name),
            data=value,
            type=record_type,
        )

    def update_dns_record(self, record, name=None, value=None):
        return self.dns_session.update_record(
            record=record,
            name=name,
            data=value
        )
