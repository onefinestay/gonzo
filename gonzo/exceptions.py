class ConfigurationError(Exception):
    pass


class CommandError(Exception):
    pass


class DataError(Exception):
    pass


class NoSuchResourceError(Exception):
    pass


class TooManyResultsError(Exception):
    pass