from gonzo.config import config_proxy as config


def get_current_cloud():
    backend = config.CLOUD['BACKEND']
    cloud_module = __import__("%s" % backend, globals(), locals(), ['Cloud'])
    return cloud_module.Cloud()
