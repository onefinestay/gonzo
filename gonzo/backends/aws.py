import datetime

import boto
from boto import ec2 as boto_ec2

from gonzo.aws.route53 import Route53
from gonzo.backends.base import BaseInstance, BaseCloud
from gonzo.config import config_proxy as config


TIME_FORMAT = '%Y-%m-%dT%H:%M:%S.000Z'


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
        r53 = Route53()
        r53.add_remove_record(self.name, "CNAME", cname)

    def terminate(self):
        self._parent.terminate()


class Cloud(BaseCloud):
    instance_class = Instance

    def _list_instances(self):
        instances = []
        for reservation in self.connection.get_all_instances():
            instances += reservation.instances
        return map(self.instance_class, instances)

    def list_security_groups(self):
        return self.connection.get_all_security_groups()

    def create_security_groups(self, groups):
        # ToDo: configurable Rules for Amazon as well.
        for sg_name, _ in groups.items():
            self.create_security_group(sg_name)

    def _region(self):
        region_name = config.REGION
        acces_key_id = config.CLOUD['AWS_ACCESS_KEY_ID']
        secret_access_key = config.CLOUD['AWS_SECRET_ACCESS_KEY']
        regions = boto.ec2.regions(
            aws_access_key_id=acces_key_id,
            aws_secret_access_key=secret_access_key)
        for region in regions:
            if region.name == region_name:
                return region
        raise KeyError("%s not found in region list" % region_name)

    _connection = None

    @property
    def connection(self):
        if self._connection is None:
            acces_key_id = config.CLOUD['AWS_ACCESS_KEY_ID']
            secret_access_key = config.CLOUD['AWS_SECRET_ACCESS_KEY']
            region = self._region()
            self._connection = boto_ec2.connection.EC2Connection(
                region=region,
                aws_access_key_id=acces_key_id,
                aws_secret_access_key=secret_access_key)
        return self._connection

    def create_security_group(self, sg_name):
        """ Creates a security group """
        sg = self.connection.create_security_group(
            sg_name, 'Rules for %s' % sg_name)
        return sg

    def get_image_by_name(self, name):
        """ Find image by name """
        images = self.connection.get_all_images(filters={
            'name': name,
        })
        if len(images) == 0:
            raise KeyError("{} not found in image list".format(name))
        if len(images) > 1:
            raise KeyError(
                "More than one image found with name {}".format(name))
        return images[0]

    def get_available_azs(self):
        """ Return a list of AZs - as single characters, no region info"""
        zones = self.connection.get_all_zones()
        azs = []
        for zone in zones:
            azs.append(zone.name[-1])

        return azs

    def get_instance_by_name(self, name):
        """ Return the instance having tag Name=name """
        try:
            return self.get_instance_by_tags(Name=name)[0]
        except IndexError:
            raise Exception("Cannot find instance named %s" % name)

    def next_az(self, server_type):
        """ Returns the next AZ to use, keeping the use of AZs balanced """

        available_azs = self.get_available_azs()
        available_azs.reverse()  # fill in a, b, c.. order, not a, z, y, x..
        filled_azs = []
        instances = self.get_instance_by_tags(server_type=server_type)
        for instance in instances:
            filled_azs.append(instance.availability_zone[-1])

        az_count, least_az = (filled_azs.count('a'), 'a')
        for az in available_azs:
            if filled_azs.count(az) < az_count:
                least_az = az

        return "%s%s" % (config.REGION, least_az)

    def launch(
            self, name, image_name, instance_type, zone,
            security_groups, key_name, tags=None):

        image = self.get_image_by_name(image_name)
        reservation = self.connection.run_instances(
            image.id, key_name=key_name,
            security_groups=security_groups,
            instance_type=instance_type,
            placement=zone
        )
        instance = self.instance_class(reservation.instances[0])
        instance.set_name(name)

        tags = tags or {}

        for tag, value in tags.items():
            instance.add_tag(tag, value)

        return instance
