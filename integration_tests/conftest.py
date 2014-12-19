import os
from urllib2 import urlparse

from fabric.api import local, settings, cd, hide
import pytest


DOCKER_IMAGE_NAME = "gonzo-integration-test"


@pytest.yield_fixture
def disable_output_capturing(request):
    # fabric doesn't work with captured outpu
    capman = request.config.pluginmanager.getplugin("capturemanager")
    original_method = capman._method

    capman._method = 'no'
    capman.reset_capturings()
    capman.init_capturings()
    try:
        yield
    finally:
        capman._method = original_method
        capman.reset_capturings()
        capman.init_capturings()


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
    import pdb; pdb.set_trace()
    if not completes_successfully('docker --version'):
        pytest.skip('docker is not available')

    if not completes_successfully(
        'docker images |grep {}'.format(DOCKER_IMAGE_NAME)
    ):
        path = os.path.dirname(__file__)
        local('docker build {} -t {}'.format(path, DOCKER_IMAGE_NAME))


def docker(cmd, *args):
    cmd = cmd.format(*args)
    return local("docker {}".format(cmd), capture=True)


@pytest.yield_fixture
def container(docker_image, disable_output_capturing):
    container = docker('run -d -P -t {} /usr/sbin/sshd -D', DOCKER_IMAGE_NAME)
    ssh_port_string = docker('port {} 22', container)
    ssh_port = ssh_port_string.split(':')[1]

    ssh_host = '127.0.0.1'

    # for boot2docker
    docker_host = os.environ.get('DOCKER_HOST')
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
    """
    Test git repo. Has a dict-like property `files` for adding/editing
    files (only supports top level files).

    >>> test_repo['requirements.txt'] = 'mypackage==0.1'
    """
    class Files(object):
        def __init__(self, path):
            self._path = path
            self._files = {}

        def __getitem__(self, key):
            return self._files[key]

        def __setitem__(self, key, value):
            self._files[key] = value
            with open(os.path.join(self._path, key), 'w') as handle:
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
        """.format()
        with cd(self.path):
            local(cmd)

        self.files = self.Files(self.path)


@pytest.fixture
def test_repo(tmpdir):
    os.chdir(str(tmpdir))
    return TestRepo(str(tmpdir))
