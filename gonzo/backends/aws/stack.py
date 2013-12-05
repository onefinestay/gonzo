from gonzo.backends.base.stack import BaseStack


class Stack(BaseStack):

    @property
    def name(self):
        return self._parent.stack_name

    @property
    def resources(self):
        return self._parent.list_resources()

    @property
    def outputs(self):
        return self._parent.outputs

    @property
    def is_complete(self):
        self._refresh()
        return self._parent.stack_status in (
            'CREATE_FAILED', 'CREATE_COMPLETE', 'ROLLBACK_FAILED',
            'ROLLBACK_COMPLETE', 'DELETE_FAILED', 'DELETE_COMPLETE',
            'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_FAILED',
            'UPDATE_ROLLBACK_COMPLETE')