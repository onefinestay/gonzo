from abc import abstractproperty
from gonzo.backends import get_current_cloud


class BaseStack(object):

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
    def resources(self):
        pass

    @abstractproperty
    def outputs(self):
        pass

    @abstractproperty
    def is_complete(self):
        pass