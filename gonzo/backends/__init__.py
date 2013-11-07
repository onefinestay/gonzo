from gonzo.config import config_proxy as config


def get_current_cloud():
    backend = config.CLOUD['BACKEND']
    cloud_module = __import__("%s" % backend, globals(), locals(), ['Cloud'])
    return cloud_module.Cloud()


class UserDataError(Exception):
    """ This exception indicates that there has been a problem either fetching
    or interpreting user data. """

    def __init__(self, msg):
        self.message = msg
