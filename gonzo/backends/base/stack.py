from abc import abstractproperty, abstractmethod
from gonzo.backends import get_current_cloud


class BaseStack(object):

    running_state = abstractproperty

    def __init__(self, stack_id):
        self._stack_id = stack_id
        self._refresh()

    def __repr__(self):
        return "<%s.%s %s>" % (
            self.__class__.__module__, self.__class__.__name__, self.id)

    def _refresh(self):
        orchestration_connection = get_current_cloud().orchestration_connection
        self._parent = orchestration_connection.describe_stacks(
            stack_name_or_id=self.id
        )[0]

    @property
    def id(self):
        return self._stack_id

    @abstractproperty
    def name(self):
        pass

    @abstractproperty
    def description(self):
        pass

    @abstractproperty
    def resources(self):
        pass

    @abstractproperty
    def outputs(self):
        pass

    @abstractproperty
    def is_complete(self):
        pass

    @abstractproperty
    def status(self):
        pass

    @abstractproperty
    def launch_time(self):
        pass

    @abstractproperty
    def region(self):
        pass

    @abstractmethod
    def delete(self):
        pass


class BaseStackResource(object):

    running_state = abstractproperty

    def __init__(self, resource_id):
        self._res_id = resource_id
        self._refresh()

    def _refresh(self):
        orchestration_connection = get_current_cloud().orchestration_connection
        self._parent = orchestration_connection.describe_stacks(
            stack_name_or_id=self.id
        )[0]