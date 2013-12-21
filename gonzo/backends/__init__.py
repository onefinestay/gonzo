from gonzo.config import config_proxy as config
from gonzo.backends.dns import get_dns_service


def get_current_cloud():
    cloud_config = config.CLOUD
    backend = cloud_config['BACKEND']
    cloud_module = __import__("%s" % backend, globals(), locals(), ['Cloud'])

    cloud = cloud_module.Cloud(
        dns_service_provider=get_dns_service()
    )

    return cloud
