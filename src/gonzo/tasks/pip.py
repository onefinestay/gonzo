from fabric.api import task, env


@task
def no_requirements():
    """ If specified, prevents push_release from pip installing requirements
        which might take a long and need bandwidth difficult to get on e.g. a
        3G connection.
    """
    env.install_requirements = False


@task
def upgrade():
    """ Cause pip to use the --upgrade flag
    """
    env.pip_upgrade = True


@task
def pip_quiet():
    """ Cause pip to use the --quiet flag
    """
    env.pip_quiet = True
