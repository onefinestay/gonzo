from abc import abstractmethod, abstractproperty

from gonzo.backends import get_dns_service


class BaseCloud(object):
    """ Wrapper for cloud providers

        provides methods for listing, adding or deleting instances,
        as well as for interacting with security groups, roles and
        availability zones
    """

    image_class = abstractproperty
    instance_class = abstractproperty
    stack_class = abstractproperty

    def __init__(self):
        self.dns = get_dns_service()

    def _instantiate_stack(self, stack_name_or_id):
        return self.stack_class(self, stack_id=stack_name_or_id)

    def _instantiate_image(self, image_id):
        return self.image_class(self, image_id=image_id)

    @abstractproperty
    def compute_connection(self):
        pass

    @abstractproperty
    def orchestration_connection(self):
        pass

    @abstractmethod
    def _list_instances(self):
        pass

    def list_instances(self, only_running=True):
        """ Return a list of all (running) instances """
        instances = self._list_instances()
        if only_running:
            instances = [i for i in instances if i.status == i.running_state]

        return instances

    @abstractmethod
    def _list_stacks(self):
        pass

    def list_stacks(self, only_running=True):
        stacks = self._list_stacks()
        if only_running:
            stacks = [s for s in stacks if s.status == s.running_state]

        return stacks

    @abstractmethod
    def get_stack(self, stack_name_or_id):
        pass

    @abstractmethod
    def list_security_groups(self):
        pass

    def get_security_group(self, name):
        """ Return the named security group """
        groups = self.list_security_groups()
        for group in groups:
            if group.name == name:
                return group

        raise Exception("Invalid security group: %s " % name)

    def security_group_exists(self, name):
        """ Returns true if the security group exists, otherwise false"""
        groups = self.list_security_groups()
        for group in groups:
            if name == group.name:
                return True

        return False

    @abstractmethod
    def create_security_group(self, sg_name):
        """ Creates a security group """
        pass

    @abstractmethod
    def create_image(self, instance, name):
        """ Capture an image of an instance and name it """

    @abstractmethod
    def delete_image(self, image):
        """ Delete a given image. """

    @abstractmethod
    def get_image_by_name(self, name):
        """ Find image by name """

    @abstractmethod
    def get_raw_image(self, image_id):
        """ Fetch an image from this cloud """

    def get_instance_by_name(self, name):
        """ Return instance having given name """
        instances = self.list_instances()
        instance = [i for i in instances if i.name == name]
        if not instance:
            raise KeyError("No instances returned with name %s" % name)
        return instance[0]

    def get_instance_by_tags(self, **tags):
        """ Return list of all instances having tags assigned as in
            keyword args.
        """
        instances = self.list_instances()
        relevant_instances = [
            i for i in instances if i.has_tags(**tags)]
        relevant_instances.sort(key=lambda i: i.name)
        return relevant_instances

    def get_instance_by_id(self, instid):
        """ Return instance having given ID """
        instance = [i for i in self.list_instances() if i.id == instid]
        if not instance:
            raise KeyError("No instances returned with ID %s" % instid)

        return instance[0]

    @abstractmethod
    def get_available_azs(self):
        """ Return a list of AZs - as single characters, no region info"""
        pass

    @abstractmethod
    def get_instance_by_dns(self, address):
        pass

    def get_instance(self, name_or_id):
        """ Return instance having name, ID or DNS name as given
            to name_or_id.
        """
        try:
            return self.get_instance_by_name(name_or_id)
        except KeyError:
            pass

        try:
            return self.get_instance_by_dns(name_or_id)
        except KeyError:
            pass

        return self.get_instance_by_id(name_or_id)

    @abstractmethod
    def next_az(self, server_type):
        """ Returns the next AZ to use, keeping the use of AZs balanced """
        pass

    @abstractmethod
    def launch_instance(
            self, name, image_name, instance_type, zone, security_groups,
            key_name, user_data=None, tags=None):
        """ Launch an instance """
        pass

    @abstractmethod
    def launch_stack(self, name, template):
        """ Launch a stack """
        pass

    @abstractmethod
    def terminate_stack(self, stack_name_or_id):
        """ Terminate a stack """
        pass
