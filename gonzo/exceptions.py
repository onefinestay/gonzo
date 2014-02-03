class ConfigurationError(Exception):
    pass


class CommandError(Exception):
    pass


class DataError(Exception):
    pass


class NoSuchResourceError(Exception):
    pass


class DNSRecordUpdateError(Exception):
    pass


class DNSRecordNotFoundError(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return 'DNS record with name "{}" not found'.format(self.name)
