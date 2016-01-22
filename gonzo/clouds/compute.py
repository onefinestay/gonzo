import logging
import time

from datetime import datetime

from libcloud.compute.types import Provider as ComputeProvider
from libcloud.compute.providers import get_driver as get_compute_driver


logger = logging.getLogger(__name__)
backends = {}


def backend_for(provider):
    def wrapper(cls):
        backends[provider] = cls
        return cls
    return wrapper


class Cloud(object):
    compute_session = None

    @classmethod
    def from_config(cls, cloud_config, region):
        try:
            backend = cloud_config['BACKEND']
        except KeyError:
            raise LookupError("No backend specified!")

        try:
            backend_cls = backends[backend]
        except KeyError:
            raise LookupError(
                "Unknown backend `{}`. Please choose one of {}".format(
                    backend, backends.keys()))
        return backend_cls(cloud_config, region)

    def list_instances(self):
        instances = self.compute_session.list_nodes()
        for instance in instances:
            self._monkeypatch_instance(instance)
        return instances

    def get_instance_by_uuid(self, instance_uuid):
        for instance in self.list_instances():
            if instance.uuid == instance_uuid:
                return instance

        raise LookupError("Instance with uuid: {} not found".format(
            instance_uuid))

    def get_instance_by_name(self, instance_name):
        for instance in self.list_instances():
            if instance.name == instance_name:
                return instance

        raise LookupError("Instance with name: {} not found".format(
            instance_name))

    def list_instances_by_type(self, environment, server_type):
        all_instances = self.list_instances()
        instances_of_type = []

        for instance in all_instances:
            metadata = self.compute_session.ex_get_metadata_for_node(
                instance)
            if (metadata.get('server_type') == server_type and
                    metadata.get('environment') == environment):
                instances_of_type.append(instance)

        instances_of_type.sort(key=lambda i: i.name)
        return instances_of_type

    def list_instance_tags(self, node):
        return node.extra[self.TAG_KEY]

    def list_availability_zones(self):
        return self.compute_session.list_locations()

    def get_next_az(self, environment, server_type):
        available_azs = self.list_availability_zones()
        try:
            newest_instance_az = self.list_instances_by_type(
                environment,
                server_type)[-1].extra['gonzo_az']
        except IndexError:
            return available_azs[0]

        if len(available_azs) == 1:
            return available_azs[0]
        else:
            for index, availabie_az in enumerate(available_azs):
                if availabie_az.name == newest_instance_az:
                    if (index + 1) == len(available_azs):
                        return available_azs[0]
                    else:
                        return available_azs[index + 1]

    def create_instance(self, image_name, name, owner, user_data=None,
                        security_groups=None, size=None, key_name=None,
                        volume_size=None, subnet_id=None):
        instance_name = name.split('-')
        environment = instance_name[0]
        server_type = '-'.join(instance_name[1:-1])

        # Image
        image = self.get_image(image_name)

        # Key Pair
        if key_name is not None:
            key = self.get_key_pair(key_name)
            key_name = key.name

        # Tags
        tags = self.generate_instance_metadata(
            owner,
            environment,
            server_type
        )

        # Instance Size
        size = self.get_instance_size_by_name(size)

        # Security Groups
        if security_groups is None:
            security_groups = []

        for index, security_group in enumerate(security_groups):
            self.create_if_not_exist_security_group(security_group, subnet_id)
            security_groups[index] = self.get_security_group(
                security_group, subnet_id
            )

        security_groups_for_launch = self.security_groups_for_launch(
            security_groups)

        # VPC Specific
        if subnet_id is not None:
            az = self.get_next_az(environment, server_type)
            subnet = self.get_subnet(subnet_id)
        else:
            az = None
            subnet = None

        # Launch Instance
        instance_dict = self._generate_instance_dict(
            name=name,
            image=image,
            size=size,
            location=az,
            ex_security_groups=security_groups_for_launch,
            ex_security_group_ids=security_groups_for_launch,
            ex_metadata=tags,
            ex_userdata=user_data,
            ex_keyname=key_name,
            ex_subnet=subnet
        )

        instance = self.compute_session.create_node(
            **instance_dict
        )

        self.compute_session.wait_until_running([instance])
        new_instance = self.get_instance_by_uuid(instance.uuid)

        if volume_size is not None:
            self.create_and_attach_volume(new_instance, volume_size)

        return new_instance

    def create_and_attach_volume(self, instance, vol_size, vol_type=None,
                                 vol_name=None):
        created_volume = self.create_volume(
            instance, instance.name,
            vol_size, vol_type)

        self.wait_until_volume_available(created_volume)

        self.compute_session.attach_volume(
            node=instance,
            volume=created_volume,
            device='/dev/xvdf'
        )

    def wait_until_volume_available(self, volume):

        while not self.volume_is_created(volume):
            time.sleep(1)
        return True

    def volume_is_created(self, volume):
        for vol in self.compute_session.list_volumes():
            if vol.id == volume.id:
                if vol.extra['state'] == 'available':
                    return True
                elif vol.extra['state'] == 'creating':
                    return False
                else:
                    raise LookupError("Unknown volume state `{}`".format(
                        vol.extra['state']))

        raise LookupError("Unknown volume `{}`".format(volume))

    def get_az_of_instance(self, instance):
        instance_az = instance.extra['gonzo_az']

        for az in self.list_availability_zones():
            if az.name == instance_az:
                return az

    def get_instance_size_by_name(self, size_name):
        for size in self.compute_session.list_sizes():
            if size_name == getattr(size, self.INSTANCE_SIZE_ATTRIBUTE):
                return size

        raise LookupError("Unknown size `{}`".format(size_name))

    def get_image(self, image_id):
            return self.compute_session.get_image(image_id)

    def get_key_pair(self, key_name):
        for key in self.compute_session.list_key_pairs():
            if key_name == key.name:
                return key
        raise LookupError("Unknown key `{}`".format(key_name))

    def generate_instance_metadata(self, owner, environment, server_type):
        instance_metadata = {}
        instance_metadata['owner'] = owner
        instance_metadata['environment'] = environment
        instance_metadata['server_type'] = server_type
        return instance_metadata

    def list_security_groups(self):
        group_list_method = getattr(self.compute_session,
                                    self.SECURITY_GROUP_METHOD)
        return group_list_method()


@backend_for('ec2')
class AWS(Cloud):
    TAG_KEY = 'tags'
    INSTANCE_SIZE_ATTRIBUTE = 'id'
    SECURITY_GROUP_IDENTIFIER = 'name'
    SECURITY_GROUP_METHOD = 'ex_get_security_groups'

    def __init__(self, cloud_config, region):

        aws_access_id = cloud_config['AWS_ACCESS_KEY_ID']
        aws_secret_key = cloud_config['AWS_SECRET_ACCESS_KEY']

        EC2Driver = get_compute_driver(ComputeProvider.EC2)
        self.compute_session = EC2Driver(
            aws_access_id, aws_secret_key, region=region)

    def _monkeypatch_instance(self, instance):
        instance.extra['gonzo_size'] = instance.extra['instance_type']
        instance.extra['gonzo_tags'] = instance.extra['tags']
        created_time = datetime.strptime(
            instance.extra['launch_time'], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        instance.extra['gonzo_created_time'] = created_time
        instance.extra['gonzo_az'] = instance.extra['availability']
        instance.extra['gonzo_network_address'] = instance.extra['dns_name']

    def security_groups_for_launch(self, security_group_names):
        vpc_id = security_group_names[0].extra['vpc_id']

        identifier = 'id' if vpc_id else 'name'

        return [
            getattr(group, identifier) for group in security_group_names
        ]

    def create_volume(self, instance, vol_name,
                      vol_size, vol_type='gp2'):
        instance_az = self.get_az_of_instance(instance)
        return self.compute_session.create_volume(
            name=vol_name,
            size=vol_size,
            location=instance_az,
            ex_volume_type=vol_type,
        )

    def create_if_not_exist_security_group(self, group_name, subnet_id=None):
        if subnet_id:
            subnet = self.compute_session.ex_list_subnets([subnet_id])[0]
            subnet_vpc = subnet.extra['vpc_id']
        else:
            subnet_vpc = None

        desc = "Rules for {}".format(group_name)
        try:
            self.compute_session.ex_create_security_group(
                group_name,
                desc,
                subnet_vpc,
            )
        except Exception as exc:  # libcloud doesn't raise anything better
            if not ("exists" in str(exc)):
                raise

    def get_subnet(self, subnet_id):
        for subnet in self.compute_session.ex_list_subnets():
            if subnet.id == subnet_id:
                return subnet
        raise LookupError("Subnet containting subnet: {} not found".format(
            subnet_id))

    def get_security_group(self, group_name, subnet_id=None):
        filters = None
        if subnet_id:
            filters = {'vpc-id': self.get_vpc_for_subnet(subnet_id)}

        sec_groups = self.compute_session.ex_get_security_groups(
            filters=filters)

        for sec_group in sec_groups:
            if sec_group.name == group_name:
                return sec_group

    def get_vpc_for_subnet(self, subnet_id):
        try:
            subnet = self.compute_session.ex_list_subnets([subnet_id])
            return subnet[0].extra['vpc_id']
        except IndexError:
            raise LookupError("VPC for subnet not found")

    def _generate_instance_dict(self, **kwargs):
        vpc_exclude = ['ex_security_groups', 'location']
        classic_exclude = ['ex_subnet', 'ex_security_group_ids']

        instance_dict = kwargs
        if instance_dict['ex_subnet']:
            for exclude in vpc_exclude:
                instance_dict.pop(exclude, None)
        else:
            for exclude in classic_exclude:
                instance_dict.pop(exclude, None)

        return instance_dict


@backend_for(ComputeProvider.OPENSTACK)
class Openstack(Cloud):
    TAG_KEY = 'metadata'
    INSTANCE_SIZE_ATTRIBUTE = 'name'
    SECURITY_GROUP_IDENTIFIER = 'name'
    SECURITY_GROUP_METHOD = 'ex_list_security_groups'

    def __init__(self, cloud_config, region):

        AUTH_URL = cloud_config['AUTH_URL']
        AUTH_USERNAME = cloud_config['USERNAME']
        AUTH_PASSWORD = cloud_config['PASSWORD']
        TENANT_NAME = cloud_config['TENANT_NAME']

        Openstack = get_compute_driver(ComputeProvider.OPENSTACK)
        self.compute_session = Openstack(AUTH_USERNAME,
                                         AUTH_PASSWORD,
                                         ex_force_auth_url=AUTH_URL,
                                         ex_tenant_name=TENANT_NAME,
                                         ex_force_auth_version="2.0_password",
                                         ex_force_service_region=region
                                         )
        self._size_cache = {}

    def _get_size_name(self, size_id):
        if size_id not in self._size_cache:
            ex_size = self.compute_session.ex_get_size(size_id)
            self._size_cache[size_id] = ex_size.name

        return self._size_cache[size_id]

    def _monkeypatch_instance(self, instance):
        instance.extra['gonzo_tags'] = instance.extra['metadata']
        instance.extra['gonzo_size'] = self._get_size_name(
            instance.extra['flavorId'])

        created_time = datetime.strptime(
            instance.extra['created'], "%Y-%m-%dT%H:%M:%S%fZ"
        )
        instance.extra['gonzo_created_time'] = created_time
        instance.extra['gonzo_az'] = instance.extra['availability_zone']
        instance.extra['gonzo_network_address'] = instance.private_ips[0]

    def security_groups_for_launch(self, security_group_names):
        return security_group_names

    def create_volume(self, instance, vol_name, vol_size, vol_type='gp2'):
        return self.compute_session.create_volume(
            name=vol_name,
            size=vol_size,
        )

    def create_if_not_exist_security_group(self, group_name, subnet_id=None):
        try:
            desc = "Rules for {}".format(group_name)
            self.compute_session.ex_create_security_group(group_name, desc)

        except Exception as exc:  # libcloud doesn't raise anything better
            if not ("exists" in str(exc)):
                raise

    def get_security_group(self, group_name, subnet_id=None):
        if subnet_id:
            raise Exception("VPC not supported for Openstack")

        for group in self.list_security_groups():
            if group_name == getattr(group, self.SECURITY_GROUP_IDENTIFIER):
                return group

    def _generate_instance_dict(self, **kwargs):

        vpc_exclude = ['ex_security_groups', 'location']

        instance_dict = kwargs
        if instance_dict['ex_subnet']:
            for exclude in vpc_exclude:
                instance_dict.pop(exclude, None)

        return instance_dict
