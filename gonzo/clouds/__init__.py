from gonzo.clouds.compute import Cloud
from gonzo.config import config_proxy


def get_current_cloud(cloud=None):
    cloud_config = config_proxy.get_cloud(cloud)
    region = config_proxy.REGION
    return Cloud.from_config(cloud_config, region)
