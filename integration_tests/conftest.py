from os import chdir, environ
from urllib2 import urlparse

from fabric.api import local, settings
import pytest


DOCKER_IMAGE_NAME = "gonzo-integration-test"


def completes_successfully(cmd):
    with settings(warn_only=True):
        res = local(cmd)
        return res.succeeded


@pytest.fixture(scope='session')
def docker_image():
    if not completes_successfully('docker --version'):
        pytest.skip('docker is not available')

    if not completes_successfully(
        'docker images |grep {}'.format(DOCKER_IMAGE_NAME)
    ):
        # TODO: more robust folder resolution
        local('docker build integration_suite -t {}'.format(DOCKER_IMAGE_NAME))


def docker(cmd, *args):
    cmd = cmd.format(*args)
    return local("docker {}".format(cmd), capture=True)


@pytest.yield_fixture
def container(docker_image):
    container = docker('run -d -P -t {} /usr/sbin/sshd -D', DOCKER_IMAGE_NAME)
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


class TestRepo(object):
    def __init__(self, path):
        self.path = path
        cmd = """
        cd {path}
        # small package with no requirements
        echo "initools==0.2" > requirements.txt
        git init
        git add requirements.txt
        git commit -m "initial add"
        git config --local gonzo.project test
        """.format(path=path)
        local(cmd)

    def add_commit(self):
        cmd = """
        cd {path}
        date >> increments.txt
        git add increments.txt
        git commit -m "increment"
        """.format(path=self.path)
        local(cmd)


@pytest.fixture
def test_repo(tmpdir):
    chdir(str(tmpdir))
    return TestRepo(tmpdir)


