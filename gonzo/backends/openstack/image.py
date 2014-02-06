from gonzo.backends.base.image import BaseImage


class Image(BaseImage):

    running_state = 'ACTIVE'

    @property
    def name(self):
        return self._parent.name

    def _refresh(self):
        self._parent = self.cloud.get_raw_image(self.id)

    @property
    def is_complete(self):
        self._refresh()
        return self._parent.status in [self.running_state]

    @property
    def is_healthy(self):
        self._refresh()
        return self._parent.status == self.running_state

    def delete(self):
        self.cloud.delete_image(self._parent)
