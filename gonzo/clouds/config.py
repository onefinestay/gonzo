from gonzo.config import config_proxy


def get_current_cloud():
    backend = config_proxy.CLOUD['BACKEND']
    cloud_module = __import__(
        "%s.cloud" % backend, globals(), locals(), ['Cloud'])
    return cloud_module.Cloud()
