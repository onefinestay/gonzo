import logging

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
            raise Exception("No backend specified!")

        try:
            backend_cls = backends[backend]
        except KeyError:
            raise Exception(
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

    def get_instance(self, instance):
        return self.compute_session.list_nodes(ex_node_ids=[instance])

    def list_instances_by_type(self, instance_type):
        all_instances = self.list_instances()
        instance_types = []

        for instance in all_instances:
            metadata = self.compute_session.ex_get_metadata_for_node(
                    instance)

            if metadata.get('server_type') == instance_type:
                instance_types.append(instance)

        instance_types.sort(key=lambda i: i.name)
        return instance_types

    def list_instance_tags(self, node):
        return node.extra[self.TAG_KEY]

    def list_availability_zones(self):
        return self.compute_session.list_locations()

    def get_next_az(self, server_type):
        #ipdb.set_trace()
        availabie_azs = self.list_availability_zones()
        try:
            newest_instance_az = self.list_instances_by_type(
                server_type)[-1].extra['gonzo_az']
        except IndexError:
            print "No Server Types Found"
            return availabie_azs[0]

        if len(availabie_azs) == 0:
            return availabie_azs
        else:
            for index, availabie_az in enumerate(availabie_azs):
                if availabie_az.name == newest_instance_az:
                    if (index + 1) == len(availabie_azs):
                        return availabie_azs[0]
                    else:
                        return availabie_azs[index + 1]

    def create_instance(self, image_name, name, owner, user_data=None,
                        security_groups=None, size=None, key_name=None):
        #ipdb.set_trace()
        instance_name = name.split('-')
        server_type = '-'.join(instance_name[1:][:-1])

        # Image
        image = self.get_image(image_name)

        # Key Pair
        if key_name is not None:
            key = self.get_key_pair(key_name)
            key_name = key.name

        # Tags
        tags = self.generate_instance_metadata(
            owner,
            environment=instance_name[0],
            server_type=server_type
            )

        # Instance Size
        size = self.get_instance_size(size, self.INSTANCE_SIZE_ATTRIBUTE)

        # Security Groups
        if security_groups is None:
            security_groups = []

        #ipdb.set_trace()
        sec_group_objects = []

        for security_group in security_groups:
            self.create_if_not_exist_security_group(security_group)
            sec_group_objects.append(self.get_security_group(security_group))

        if not self.SECURITY_GROUP_OBJECT:
            security_groups = []
            for sec_group in sec_group_objects:
                security_groups.append(getattr(sec_group,
                                               self.SECURITY_GROUP_IDENTIFIER))
        else:
            security_groups = sec_group_objects

        # Availability Zone
        az = self.get_next_az(server_type)

        # Launch Instance
        instance = self.compute_session.create_node(
            name=name,
            image=image,
            size=size,
            location=az,
            ex_security_groups=security_groups,
            ex_metadata=tags,
            ex_userdata=user_data,
            ex_keyname=key_name,
            )
        self.compute_session.wait_until_running([instance])
        new_instance = self.get_instance_by_uuid(instance.uuid)
       # ipdb.set_trace()
        return new_instance

    def get_instance_size(self, size_name, query_attribute):
        for size in self.compute_session.list_sizes():
            if size_name == getattr(size, query_attribute):
                return size

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

    def add_default_security_groups(server_type,
                                    additional_security_groups=None):
        # Set defaults
        security_groups = [server_type, 'gonzo']

        # Add argument passed groups
        if additional_security_groups is not None:
            security_groups += additional_security_groups

        # Remove Duplicates
        security_groups = list(set(security_groups))
        return security_groups

    def create_if_not_exist_security_group(self, group_name):

        try:
            desc = "Rules for {}".format(group_name)
            self.compute_session.ex_create_security_group(group_name, desc)

        except Exception as exc:  # libcloud doesn't raise anything better
            if not ("exists" in str(exc)):
                raise
            print "Security Group {} Exists".format(group_name)

    def get_security_group(self, group_name):

        for group in self.list_security_groups():
            if group_name == getattr(group, self.SECURITY_GROUP_IDENTIFIER):
                print "Sec Group Matched!"
                return group

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
    SECURITY_GROUP_OBJECT = False

    def __init__(self, cloud_config, region):

        aws_access_id = cloud_config['AWS_ACCESS_KEY_ID']
        aws_secret_key = cloud_config['AWS_SECRET_ACCESS_KEY']

        EC2Driver = get_compute_driver(ComputeProvider.EC2)
        self.compute_session = EC2Driver(
            aws_access_id, aws_secret_key, region=region)

    def _monkeypatch_instance(self, instance):
        instance.extra['gonzo_size'] = instance.extra['instance_type']
        instance.extra['gonzo_tags'] = instance.extra['tags']
        instance.extra['gonzo_created_time'] = instance.extra['launch_time']
        instance.extra['gonzo_az'] = instance.extra['availability']
        instance.extra['gonzo_network_address'] = instance.extra['dns_name']

@backend_for(ComputeProvider.OPENSTACK)
class Openstack(Cloud):

    TAG_KEY = 'metadata'
    INSTANCE_SIZE_ATTRIBUTE = 'name'
    SECURITY_GROUP_IDENTIFIER = 'name'
    SECURITY_GROUP_METHOD = 'ex_list_security_groups'
    SECURITY_GROUP_OBJECT = True

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

    def _monkeypatch_instance(self, instance):
        instance.extra['gonzo_tags'] = instance.extra['metadata']

        size = self.get_instance_size(instance.extra['flavorId'], "id")

        instance.extra['gonzo_size'] = getattr(size,
                                               self.INSTANCE_SIZE_ATTRIBUTE)

        instance.extra['gonzo_created_time'] = instance.extra['created']
        instance.extra['gonzo_az'] = instance.extra['availability_zone']
        instance.extra['gonzo_network_address'] = instance.private_ips[0]

# backends['openstack'] = Openstack


class InstanceExtra(object):
    def __init__(self, data, size):
        self.data = data
        self.size = size

    @property
    def created_at(self):
        return self.data[self.CREATION_TIME_ATTR]

    @property
    def tags(self):
        return self.data[self.TAGS_ATTR]


class AwsInstanceExtra(InstanceExtra):
    TAGS_ATTR = 'tags'
    CREATION_TIME_ATTR = 'launch_time'


class OpenstackInstanceExtra(InstanceExtra):
    @property
    def tags(self):
        return self.data['metadata']
