class ConfigurationError(Exception):
    pass


class DataError(Exception):
    pass


class NoSuchResourceError(Exception):
    pass


class MultipleResourcesError(Exception):
    pass


class UnhealthyResourceError(Exception):
    pass
