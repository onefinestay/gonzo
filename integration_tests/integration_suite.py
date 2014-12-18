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

py.test integration_tests/integration_suite.py

"""

import shutil
import tempfile
from contextlib import contextmanager
from os import chdir, environ
from urllib2 import urlparse

from fabric.api import local, settings
import pytest

from gonzo.tasks.release import activate, list_releases, push

image = "gonzo-integration-test"


def completes_successfully(cmd):
    with settings(warn_only=True):
        res = local(cmd)
        return res.succeeded


@pytest.fixture(scope='session')
def docker_image():
    if not completes_successfully('docker --version'):
        pytest.skip('docker is not available')

    if not completes_successfully(
        'docker images |grep gonzo-integration-test'
    ):
        # TODO: more robust folder resolution
        local('docker build integration_suite -t gonzo-integration-test')


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
echo "initools==0.2" > requirements.txt  # small package with no requirements
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
    return local("docker {}".format(cmd), capture=True)


@contextmanager
def temp_container(image_name):
    container = docker('run -d -P -t {} /usr/sbin/sshd -D', image)
    ssh_port_string = docker('port {} 22', container)
    ssh_port = ssh_port_string.split(':')[1]

    ssh_host = '127.0.0.1'

    # for boot2docker
    docker_host = environ.get('DOCKER_HOST')
    if docker_host:
        parsed = urlparse.urlparse(docker_host)
        ssh_host = parsed.hostname

    container_host = 'gonzo@{}:{}'.format(ssh_host, ssh_port)

    try:
        with settings(
            user="root",
            password="password",
            host_string=container_host,
        ):
            yield container

    finally:
        docker('kill {}', container)
        docker('rm {}', container)


def test_basic(docker_image):
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
            assert len(history) == 2
