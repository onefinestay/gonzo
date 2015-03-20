from __future__ import absolute_import  # otherwise we find ourself

import envoy
from fabric.api import env, task

from gonzo.clouds import get_current_cloud
from gonzo.config import config_proxy as config


def resolve_int_dns(name):
    """ turn into an DNS_ZONE hostname if resolvable """
    hostname = "{}.{}".format(name, config.CLOUD['DNS_ZONE'])
    hostname = str(hostname)
    dig = envoy.run("dig {} +short".format(hostname))

    if len(dig.std_out):
        return hostname
    else:
        return None


def get_hostname(inst):
    """ return a nice hostname (DNS_ZONE) if available, or fall back
        to internal address"""

    fallback = inst.internal_address()
    name = inst.name
    if name is None:
        return fallback

    hostname = resolve_int_dns(name)
    if hostname is None:
        return fallback

    return hostname


@task
def instance(*names):
    """ Set hosts to be that having the tags Name set to each of the
        arguments. Takes multiple names.
    """

    cloud = get_current_cloud()
    for name in names:
        inst = cloud.get_instance_by_name(name)
        dns_name = get_hostname(inst)
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

        instances = cloud.get_instance_by_tags(
            environment=environment, server_type=server_type)
        env.hosts.extend([get_hostname(inst) for inst in instances])

    print env.hosts
