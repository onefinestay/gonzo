"""
Integration suite
=================

Beginnings of a docker-based integration suite


Requirements
------------

docker


Setup
-----

build base image::

    docker build . -t gonzo-integration-test


Run tests
---------

python integration_suite.py

"""

import shutil
import tempfile
from contextlib import contextmanager
from os import chdir
from time import sleep

from fabric.api import local, settings, sudo, task
from gonzo.tasks.release import activate, list_releases, push

image = "gonzo-integration-test"


@contextmanager
def tempdir():
    """Simple context that provides a temporary directory that is deleted
    when the context is exited.
    """
    folder = tempfile.mkdtemp(".tmp", "gonzo.")
    try:
        yield folder
    finally:
        shutil.rmtree(folder)


def make_test_repo(path):
    cmd = """
cd {path}
echo "bottle" > requirements.txt  # small package with no requirements
git init
git add requirements.txt
git commit -m "initial add"
git config --local gonzo.project test
""".format(path=path)
    local(cmd)

def add_commit(path):
    cmd = """
cd {path}
date >> increments.txt
git add increments.txt
git commit -m "increment"
""".format(path=path)
    local(cmd)


def docker(cmd, *args):
    cmd = cmd.format(*args)
    return local("sudo docker {}".format(cmd), capture=True)


@contextmanager
def temp_container(image_name):
    container = docker('run -d -p 22 {} /usr/sbin/sshd -D', image)
    ssh_port = docker('port {} 22', container)

    container_host = 'gonzo@localhost:{}'.format(ssh_port)
    sleep(1)  # give it time to start

    try:
        with settings(
            user="root",
            password="password",
            host_string=container_host,
        ):
            # sudo complains if it cannot resolve itself
            sudo('echo "127.0.0.1 localhost {}" >> /etc/hosts'.format(
                container))

            yield container

    finally:
        docker('kill {}', container)
        docker('rm {}', container)


@task
def test():
    with tempdir() as path:
        make_test_repo(path)
        chdir(path)

        with temp_container(image):
            push()
            activate()
            add_commit(path)
            push()
            activate()
            add_commit(path)
            push()
            history = list_releases()
            print "history", history


if __name__ == '__main__':
    test()
