from libcloud.dns.providers import get_driver as get_dns_driver
from libcloud.dns.types import Provider as DNSProvider


class DNS(object):

    def __init__(self, aws_access_id, aws_secret_key):
        R53Driver = get_dns_driver(DNSProvider.ROUTE53)
        self.dns_session = R53Driver(aws_access_id, aws_secret_key)

    def get_next_host(self, server_name, zone_name):
        count_record = "_count-{}".format(server_name)
        record = self.get_dns_record(count_record, zone_name)

        if record:
            next_count = int(record.data.strip('"')) + 1
            self.update_dns_record(
                record=record,
                value='"{}"'.format(next_count),
            )
        else:
            next_count = 1
            self.create_dns_record(
                name=count_record,
                value='"{}"'.format(next_count),
                record_type="TXT",
                zone_name=zone_name
            )
        return "%s-%03d" % (server_name, next_count)

    def get_zone(self, zone_name):
        for zone in self.dns_session.iterate_zones():
            if zone_name == zone.domain[:-1]:
                return zone

    def get_dns_record(self, record_name, zone):
        for dns_record in self.dns_session.iterate_records(
                self.get_zone(zone)):
            if record_name == dns_record.name:
                return dns_record

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
