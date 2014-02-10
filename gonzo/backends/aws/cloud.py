import boto
from boto import ec2 as boto_ec2
from boto import cloudformation as boto_cfn

from gonzo.backends.aws.image import Image
from gonzo.backends.aws.instance import Instance
from gonzo.backends.aws.stack import Stack
from gonzo.backends.base.cloud import BaseCloud
from gonzo.config import config_proxy as config
from gonzo.exceptions import NoSuchResourceError, TooManyResultsError


class Cloud(BaseCloud):
    instance_class = Instance
    stack_class = Stack
    image_class = Image

    def _list_instances(self):
        instances = []
        for reservation in self.compute_connection.get_all_instances():
            instances += reservation.instances
        return map(self.instance_class, instances)

    def _list_stacks(self):
        stacks = self.orchestration_connection.list_stacks()
        return map(self._instantiate_stack, [s.stack_id for s in stacks])

    def get_stack(self, stack_name_or_id):
        potential_stacks = self.orchestration_connection.describe_stacks(
            stack_name_or_id=stack_name_or_id)

        return self._instantiate_stack(potential_stacks[0].stack_id)

    def list_security_groups(self):
        return self.compute_connection.get_all_security_groups()

    def _credentials(self):
        return {
            'aws_access_key_id': config.CLOUD['AWS_ACCESS_KEY_ID'],
            'aws_secret_access_key': config.CLOUD['AWS_SECRET_ACCESS_KEY'],
        }

    def _ec2_regions(self):
        return boto_ec2.regions(**self._credentials())

    def _cfn_regions(self):
        return boto_cfn.regions()

    def _region(self, regions):
        region_name = config.REGION
        for region in regions:
            if region.name == region_name:
                return region
        raise KeyError("%s not found in region list" % region_name)

    _compute_connection = None

    @property
    def compute_connection(self):
        if self._compute_connection is None:
            region = self._region(self._ec2_regions())
            self._compute_connection = boto.connect_ec2(
                region=region,
                **self._credentials()
            )
        return self._compute_connection

    _orchestration_connection = None

    @property
    def orchestration_connection(self):
        if self._orchestration_connection is None:
            region = self._region(self._cfn_regions())
            self._orchestration_connection = boto.connect_cloudformation(
                region=region,
                **config.CLOUD['ORCHESTRATION_CREDENTIALS']
            )
        return self._orchestration_connection

    def create_security_group(self, sg_name):
        """ Creates a security group """
        sg = self.compute_connection.create_security_group(
            sg_name, 'Rules for %s' % sg_name)
        return sg

    def create_image(self, instance, name):
        self.compute_connection.create_image(instance.id, name, no_reboot=True)
        return self.get_image_by_name(name)

    def delete_image(self, image):
        self.compute_connection.deregister_image(
            image.id, delete_snapshot=True)

    def get_image_by_name(self, name):
        """ Find image by name """
        raw_images = self.compute_connection.get_all_images(filters={
            'name': name,
        })
        if len(raw_images) == 0:
            raise NoSuchResourceError(
                "No images found with name {}".format(name))
        if len(raw_images) > 1:
            raise TooManyResultsError(
                "More than one image found with name {}".format(name))

        return self._instantiate_image(raw_images[0].id)

    def get_raw_image(self, image_id):
        """ Find image by id """
        return self.compute_connection.get_image(image_id)

    def get_available_azs(self):
        """ Return a list of AZs - as single characters, no region info"""
        zones = self.compute_connection.get_all_zones()
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

    def launch_instance(
            self, name, image_name, instance_type, zone,
            security_groups, key_name, user_data=None, tags=None):

        image = self.get_image_by_name(image_name)

        reservation = self.compute_connection.run_instances(
            image.id, key_name=key_name,
            security_groups=security_groups,
            instance_type=instance_type,
            placement=zone, user_data=user_data
        )
        instance = self.instance_class(reservation.instances[0])
        instance.set_name(name)

        tags = tags or {}

        for tag, value in tags.items():
            instance.add_tag(tag, value)

        return instance

    def launch_stack(self, name, template):
        stack_id = self.orchestration_connection.create_stack(
            stack_name=name,
            template_body=template,
        )

        return self._instantiate_stack(stack_id)

    def terminate_stack(self, stack_name_or_id):
        stack = self._instantiate_stack(stack_name_or_id)
        stack.delete()
        return stack
