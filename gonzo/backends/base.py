from abc import abstractmethod, abstractproperty


class BaseInstance(object):
    """ Wrapper for ec2 or openstack instances """
    running_state = abstractproperty

    def __init__(self, parent):
        self._parent = parent

    def __repr__(self):
        return "<%s.%s %s>" % (
            self.__class__.__module__, self.__class__.__name__, self.name)

    @property
    def id(self):
        return self._parent.id

    @abstractproperty
    def name(self):
        pass

    @abstractproperty
    def tags(self):
        pass

    @abstractproperty
    def region_name(self):
        pass

    @abstractproperty
    def groups(self):
        pass

    @abstractproperty
    def availability_zone(self):
        pass

    @abstractproperty
    def instance_type(self):
        pass

    @abstractproperty
    def launch_time(self):
        pass

    @abstractproperty
    def status(self):
        pass

    def is_running(self):
        return self.status == self.running_state

    # TODO: just have a dict-like `tags` attribute?

    @abstractmethod
    def add_tag(self, key, value):
        pass

    @abstractmethod
    def set_name(self, name):
        pass

    def has_tags(self, **tags):
        """ Utility; returns True if the given instance has the specified tags
            set as per the keyword args."""
        for key, value in tags.items():
            try:
                if self.tags[key] != value:
                    return False
            except KeyError:
                return False

        return True

    @abstractmethod
    def internal_address(self):
        pass

    @abstractmethod
    def create_dns_entry(self):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def terminate(self):
        pass


class BaseCloud(object):
    instance_class = abstractproperty

    @abstractproperty
    def connection(self):
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
    def list_security_groups(self):
        pass

    @abstractmethod
    def list_images(self):
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

    def get_image(self, name):
        images = self.list_images()
        for image in images:
            if image.name == name:
                return image
        raise KeyError("%s not found in image list" % name)

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

    def get_instances_by_env(self, env):
        """ Return a list of instances matching the environment specified """
        try:
            instances = self.get_instance_by_tags(env=env)
        except:
            raise KeyError("%s not found in instance list" % env)

        return instances

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
    def next_az(self, env):
        """ Returns the next AZ to use, keeping the use of AZs balanced """
        pass

    @abstractmethod
    def launch(
            self, name, image_name, instance_type, zone, security_groups,
            key_name, tags=None):
        pass
