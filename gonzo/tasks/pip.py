from __future__ import absolute_import  # otherwise we find tasks.gonzo

from fabric.api import task, env


@task
def index_url(url):
    """ Use a custom index-url when running `pip install`
    """
    env.pip_index_url = url


@task
def quiet():
    """ Cause pip to use the --quiet flag when pushing new releases
    """
    env.pip_quiet = True
