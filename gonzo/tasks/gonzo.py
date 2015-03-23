from __future__ import absolute_import  # otherwise we find ourself

from fabric.api import env, task

from gonzo.clouds import get_current_cloud
from gonzo.config import config_proxy as config


def get_hostname_dns(inst):
    return "{}.{}".format(inst.name, config.CLOUD['DNS_ZONE'])


@task
def instance(*names):
    """ Set hosts to be that having the tags Name set to each of the
        arguments. Takes multiple names.
    """

    cloud = get_current_cloud()
    for name in names:
        inst = cloud.get_instance_by_name(name)
        dns_name = get_hostname_dns(inst)
        env.hosts.append(dns_name)

    print env.hosts


@task
def group(*env_type_pairs):
    """ Set hosts by group (environment-server_type) """

    cloud = get_current_cloud()
    for env_type_pair in env_type_pairs:
        # env_type_pair is e.g. produiction-platform-app
        # we want production, and platform-app
        environment, server_type = env_type_pair.split("-", 1)
        instances = cloud.list_instances_by_type(
            environment=environment, instance_type=server_type)
        env.hosts.extend([get_hostname_dns(inst) for inst in instances])

    print env.hosts
