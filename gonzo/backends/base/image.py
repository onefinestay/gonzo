class BaseImage(object):

    available_state = 'ACTIVE'

    def __init__(self, cloud, image_id=None):
        self.cloud = cloud
        self.id = image_id
        self._refresh()

    def __repr__(self):
        return "<%s.%s %s>" % (
            self.__class__.__module__, self.__class__.__name__, self.id)

    @property
    def name(self):
        return self._parent.name

    def _refresh(self):
        """ responsible for updating the details of this resource from the
        resource's cloud """
        self._parent = self.cloud.get_raw_image(self.id)

    @property
    def is_complete(self):
        self._refresh()
        return self._parent.status in [self.available_state, 'FAILED']

    @property
    def is_healthy(self):
        self._refresh()
        return self._parent.status == self.available_state

    def delete(self):
        self.cloud.delete_image(self._parent)
