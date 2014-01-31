from abc import abstractproperty, abstractmethod

from gonzo.aws.route53 import Route53


class BaseInstance(object):
    """ Wrapper for cloud instances

        Interrogate these for name, tags and other properties
    """
    running_state = abstractproperty
    internal_address_dns_type = abstractproperty

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
        """ Instance name """
        pass

    @abstractproperty
    def tags(self):
        """ Instance tags """
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

    def create_dns_entry(self, name=None):
        address = self.internal_address()
        record_type = self.internal_address_dns_type
        if name is None:
            name = self.name
        r53 = Route53()
        r53.add_remove_record(name, record_type, address)

    def create_dns_entries_from_tag(self, key='cnames'):
        if key not in self.tags:
            return
        names = self.tags[key].split(',')
        for name in names:
            self.create_dns_entry(name)

    def delete_dns_entries(self):
        r53 = Route53()
        value = self.internal_address()
        r53.delete_dns_by_value(value)

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def terminate(self):
        pass
