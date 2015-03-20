from gonzo.clouds.compute import Cloud
from gonzo.config import config_proxy


def get_current_cloud():
    cloud_config = config_proxy.CLOUD
    region = config_proxy.REGION
    return Cloud.from_config(cloud_config, region)
