from gonzo.config import config_proxy as config


__all__ = ["cloud"]


backend = config.CLOUD['BACKEND']
cloud_module = __import__("%s" % backend, globals(), locals(), ['Cloud'])
cloud = cloud_module.Cloud()
