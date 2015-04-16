from __future__ import absolute_import  # otherwise we find tasks.gonzo

from fabric.api import sudo, task


@task
def update(dry_run=None):
    """ Force a puppet update """
    # appending true is a hack because puppet, it seems, returns code
    # 2 if it has changed something. This, of course, is deeply wrong
    # and, of course, causes fab to bail because it assumes, not
    # unreasonably, that there has been an error.
    puppetargs = [
        "",
        "onetime",
        "ignorecache",
        "no-daemonize",
        "no-usecacheonfailure",
        "no-splay",
        "verbose",
    ]

    if dry_run is not None:
            puppetargs.append("noop")

    sudo("puppet agent %s " % " --".join(puppetargs))


@task
def status():
    """ Return the status of puppet """
    sudo('/etc/init.d/puppet status; true')
    sudo('ps aux | grep puppet | grep -v grep; true')


@task
def start():
    """Start puppet"""
    sudo('/etc/init.d/puppet start; true')


@task
def stop():
    """Stop puppet"""
    sudo('/etc/init.d/puppet stop; true')


@task
def restart():
    """ Re-start the puppet daemon. Do not call this on a node which you plan
        making into an AMI as you will trigger installation of packages which
        may not be appropriate.
    """
    sudo("/etc/init.d/puppet restart; sleep 2")
