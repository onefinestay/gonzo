from __future__ import absolute_import  # otherwise we find tasks.gonzo

from fabric.api import task, env


@task
def flags(flags):
    """ Add custom flags to pip when installing requirements.txt

    Example:
        pip.flags:'--index-url=https://mypi.example.com --quiet'
    """
    env.pip_flags = flags
