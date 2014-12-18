from __future__ import absolute_import  # otherwise we find tasks.gonzo

from fabric.api import task, env


@task
def pip_quiet():
    """ Cause pip to use the --quiet flag when pushing new releases
    """
    env.pip_quiet = True
