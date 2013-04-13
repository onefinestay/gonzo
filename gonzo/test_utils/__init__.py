

# getting these names wrong on the mocks will result in always passing tests
# instead of calling methods on the mock, call these (where typos will fail)

def assert_called_once_with(mock, *args, **kwargs):
    mock.assert_called_once_with(*args, **kwargs)


def assert_called_with(mock, *args, **kwargs):
    mock.assert_called_with(*args, **kwargs)


def assert_has_calls(mock, *args, **kwargs):
    mock.assert_has_calls(*args, **kwargs)
