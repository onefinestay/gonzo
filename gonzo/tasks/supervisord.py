from fabric.api import sudo, task


@task
def reload():
    """ Reload the supervisord conf.d files and restart all programs """
    sudo("supervisorctl reload; sleep 5")
    status()


@task
def status():
    """ Return the status of all process being supervised """
    sudo("supervisorctl status")


@task
def update():
    """ re read the config """
    sudo("supervisorctl update")


@task
def restart(service):
    """ Restarts the sevice """
    sudo("supervisorctl restart %s" % service)
    status()

