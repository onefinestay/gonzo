from abc import abstractproperty, abstractmethod


class BaseImage(object):

    available_state = abstractproperty

    def __init__(self, cloud, image_id=None):
        self.cloud = cloud
        self.id = image_id
        self._refresh()

    def __repr__(self):
        return "<%s.%s %s>" % (
            self.__class__.__module__, self.__class__.__name__, self.id)

    @abstractproperty
    def name(self):
        pass

    @abstractmethod
    def _refresh(self):
        """ responsible for updating the details of this resource from the
        resource's cloud """

    @abstractproperty
    def is_complete(self):
        pass

    @abstractproperty
    def is_healthy(self):
        pass

    @abstractmethod
    def delete(self):
        pass
