from os import chdir, environ, path
from urllib2 import urlparse

from fabric.api import local, settings, cd, hide
import pytest


DOCKER_IMAGE_NAME = "gonzo-integration-test"


@pytest.fixture(autouse=True)
def disable_output_capturing(request):
    capture_config = request.config.getoption('capture')
    if capture_config != 'no':
        pytest.fail('fabric requires --capture=no/-s')


@pytest.yield_fixture(autouse=True)
def hide_fabric_output(request):
    if request.config.getoption('verbose') == 0:
        groups = ['running', 'stdout', 'stderr']
    else:
        groups = []

    with hide(*groups):
        yield


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
    class Files(object):
        def __init__(self, path):
            self._path = path
            self._files = {}

        def __getitem__(self, key):
            return self._files[key]

        def __setitem__(self, key, value):
            self._files[key] = value
            with open(path.join(self._path, key), 'w') as handle:
                handle.write(value)
            cmd = """
                git add {key}
                git commit -m "updated {key}"
            """.format(key=key)
            with cd(self._path):
                local(cmd)

    def __init__(self, path):
        self.path = path
        cmd = """
        echo "test repo" > readme.txt
        git init
        git add readme.txt
        git commit -m "initial add"
        git config --local gonzo.project test
        """.format(path=path)
        with cd(self.path):
            local(cmd)

        self.files = self.Files(self.path)


@pytest.fixture
def test_repo(tmpdir):
    chdir(str(tmpdir))
    return TestRepo(str(tmpdir))


