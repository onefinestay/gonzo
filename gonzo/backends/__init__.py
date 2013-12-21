from gonzo.backends.dns import get_dns_service
from gonzo.config import config_proxy as config


def get_current_cloud():
    backend = config.CLOUD['BACKEND']
    cloud_module = __import__("%s" % backend, globals(), locals(), ['Cloud'])

    cloud = cloud_module.Cloud(
        dns_service_provider=get_dns_service()
    )

    return cloud
