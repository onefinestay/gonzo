from fabric.api import sudo, task


@task
def restart():
    """ Re-start apache server """
    sudo("/etc/init.d/apache2 restart; sleep 2")


@task
def graceful():
    """ Re-start apache server gracefully - children finish responding """
    sudo("/etc/init.d/apache2 graceful; sleep 2")
