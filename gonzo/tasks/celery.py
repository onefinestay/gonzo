from fabric.api import sudo, task


@task
def restart():
    """Restart Celery and Celerybeat"""
    sudo("/etc/init.d/celeryd restart; sleep 5")
    sudo("/etc/init.d/celerybeat restart; sleep 5")
