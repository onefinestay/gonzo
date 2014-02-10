from abc import abstractproperty, abstractmethod
from boto.exception import BotoServerError

from gonzo.config import config_proxy as config
from gonzo.exceptions import NoSuchResourceError, MultipleResourcesError


class BaseStack(object):

    running_state = abstractproperty

    def __init__(self, cloud, stack_id=None):
        self.cloud = cloud
        self._stack_id = stack_id
        self._refresh()

    def __repr__(self):
        return "<%s.%s %s>" % (
            self.__class__.__module__, self.__class__.__name__, self.id)

    def _refresh(self):
        orchestration_connection = self.cloud.orchestration_connection
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

    @abstractmethod
    def get_resource(self, physical_resource_id):
        pass

    @abstractmethod
    def create_or_update_images(self):
        pass

    @abstractproperty
    def outputs(self):
        pass

    @abstractproperty
    def is_complete(self):
        pass

    @abstractproperty
    def is_healthy(self):
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

    @abstractmethod
    def get_instances(self):
        pass


class BotoCfnStack(BaseStack):

    running_state = 'CREATE_COMPLETE'
    instance_type = 'AWS::EC2::Instance'

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
        orchestration_connection = self.cloud.orchestration_connection
        return orchestration_connection.describe_stack_resources(
            stack_name_or_id=self.name,
        )

    def get_resource(self, physical_resource_id):
        resources = [resource for resource in self.resources
                     if resource.physical_resource_id == physical_resource_id]

        if len(resources) == 0:
            raise NoSuchResourceError(
                "Could not find stack resource with physical id {}".format(
                    physical_resource_id))

        if len(resources) > 1:
            raise MultipleResourcesError(
                "Found more that one resource with physical id {}".format(
                    physical_resource_id))

        return resources[0]

    def create_or_update_images(self):
        requested_images = []
        for instance in self.get_instances():
            instance_resource = self.get_resource(
                physical_resource_id=instance.id)
            image_name = instance_resource.logical_resource_id

            try:
                existing_image = self.cloud.get_image_by_name(image_name)
                existing_image.delete()
            except NoSuchResourceError:
                pass

            requested_images.append(
                self.cloud.create_image(instance, image_name))

        return requested_images

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

    @property
    def is_healthy(self):
        return self.is_complete and \
            self._parent.stack_status == self.running_state

    def delete(self):
        self._parent.delete()

    def get_instances(self):
        instance_refs = [res for res in self.resources
                         if res.resource_type == self.instance_type]

        return [self.cloud.get_instance_by_id(ref.physical_resource_id)
                for ref in instance_refs]
