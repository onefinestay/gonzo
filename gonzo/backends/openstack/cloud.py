from urlparse import urlparse
from boto.cloudformation import connection as cfn_boto
from boto import regioninfo

from novaclient.v1_1 import client as nova_client
from novaclient.exceptions import NoUniqueMatch, NotFound

from gonzo.backends.base.cloud import BaseCloud
from gonzo.backends.openstack import OPENSTACK_AVAILABILITY_ZONE
from gonzo.config import config_proxy as config
from gonzo.backends.openstack.instance import Instance
from gonzo.backends.openstack.stack import Stack


class Cloud(BaseCloud):

    instance_class = Instance
    stack_class = Stack

    def _list_instances(self):
        instances = self.compute_connection.list()
        return map(self.instance_class, instances)

    def list_security_groups(self):
        return self.compute_connection.api.security_groups.list()

    def _list_instance_types(self):
        return self.compute_connection.api.flavors.list()

    def _list_stacks(self):
        stacks = self.orchestration_connection.list_stacks()
        return map(self.stack_class, [s.stack_id for s in stacks])

    def get_stack(self, stack_name_or_id):
        potential_stacks = self.orchestration_connection.describe_stacks(
            stack_name_or_id=stack_name_or_id)

        return self.stack_class(potential_stacks[0].stack_id)

    def create_security_group(self, sg_name):
        """ Creates a security group """
        sg = self.compute_connection.api.security_groups.create(
            sg_name, 'Rules for %s' % sg_name)
        return sg

    def get_image_by_name(self, name):
        """ Find image by name """
        try:
            return self.compute_connection.api.images.find(name=name)
        except (NotFound, NoUniqueMatch):
            # in case we want to do/throw something else later
            raise

    def get_available_azs(self):
        """ Return a list of AZs - as single characters, no region info"""
        return [OPENSTACK_AVAILABILITY_ZONE]

    _compute_connection = None

    @property
    def compute_connection(self):
        if self._compute_connection is None:

            client = nova_client.Client(
                config.CLOUD['USERNAME'],
                config.CLOUD['PASSWORD'],
                config.CLOUD['TENANT_NAME'],
                config.CLOUD['AUTH_URL'],
                service_type="compute")
            self._compute_connection = client.servers
        return self._compute_connection

    _orchestration_connection = None

    @property
    def orchestration_connection(self):
        if self._orchestration_connection is None:
            split_url = urlparse(config.CLOUD['ORCHESTRATION_URL'])
            is_secure = split_url.scheme == 'https'

            self._orchestration_connection = cfn_boto.CloudFormationConnection(
                region=regioninfo.RegionInfo(
                    name="heat",
                    endpoint=split_url.hostname),
                port=split_url.port,
                is_secure=is_secure,
                path=split_url.path,
                **config.CLOUD['ORCHESTRATION_CREDENTIALS'])
        return self._orchestration_connection

    def _get_instance_type(self, name):
        flavours = self._list_instance_types()
        for flavour in flavours:
            if flavour.name == name:
                return flavour
        raise KeyError("%s not found in instance type list" % name)

    def next_az(self, server_type):
        """ Returns the next AZ to use, keeping the use of AZs balanced """
        return OPENSTACK_AVAILABILITY_ZONE

    def launch(
            self, name, image_name, instance_type, zone,
            security_groups, key_name, user_data=None, tags=None):
        image = self.get_image_by_name(image_name)
        flavour = self._get_instance_type(instance_type)

        raw_instance = self.compute_connection.create(
            name, image.id, flavor=flavour.id, availability_zone=zone,
            security_groups=security_groups, key_name=key_name, meta=tags,
            userdata=user_data)

        instance = self.instance_class(raw_instance)

        return instance

    def launch_stack(self, name, template):
        stack_id = self.orchestration_connection.create_stack(
            stack_name=name,
            template_body=template,
        )

        return self.stack_class(stack_id)

    def terminate_stack(self, stack_name_or_id):
        stack = self.stack_class(stack_name_or_id)
        stack.delete()
        return stack
