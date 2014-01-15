from abc import abstractproperty, abstractmethod
from boto.exception import BotoServerError

from gonzo.backends import get_current_cloud
from gonzo.config import config_proxy as config
from gonzo.exceptions import NoSuchResourceError


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


class BotoCfnStack(BaseStack):

    running_state = 'CREATE_COMPLETE'

    @property
    def description(self):
        return self._parent.description

    @property
    def status(self):
        return self._parent.stack_status

    @property
    def region(self):
        return config.REGION

    @property
    def launch_time(self):
        return self._parent.creation_time

    @property
    def name(self):
        return self._parent.stack_name

    @property
    def resources(self):
        orchestration_connection = get_current_cloud().orchestration_connection
        return orchestration_connection.describe_stack_resources(
            stack_name_or_id=self.name,
        )

    @property
    def outputs(self):
        return self._parent.outputs

    @property
    def is_complete(self):
        try:
            self._refresh()
            return self._parent.stack_status in (
                'CREATE_FAILED', 'CREATE_COMPLETE', 'ROLLBACK_FAILED',
                'ROLLBACK_COMPLETE', 'DELETE_FAILED', 'DELETE_COMPLETE',
                'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_FAILED',
                'UPDATE_ROLLBACK_COMPLETE')
        except BotoServerError as err:
            if err.error_message.__contains__('could not be found'):
                raise NoSuchResourceError
            else:
                raise err

    def delete(self):
        self._parent.delete()
