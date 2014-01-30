from abc import abstractproperty, abstractmethod

from gonzo.backends import get_current_cloud


class BaseInstance(object):
    """ Wrapper for cloud instances

        Interrogate these for name, tags and other properties
    """
    running_state = abstractproperty

    def __init__(self, parent):
        self._parent = parent
        self._cloud = get_current_cloud()

    def __repr__(self):
        return "<%s.%s %s>" % (
            self.__class__.__module__, self.__class__.__name__, self.name)

    @property
    def id(self):
        return self._parent.id

    @property
    def cloud(self):
        return self._cloud

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

    @abstractmethod
    def create_dns_entry(self):
        pass

    @abstractmethod
    def create_dns_entries_from_tag(self, key, delimiter=','):
        pass

    @abstractmethod
    def delete_dns_entries(self):
        pass

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def terminate(self):
        pass
