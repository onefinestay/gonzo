import pytest
from mock import Mock, patch

from gonzo.config import get_reader, get_writer, set_option, \
        get_option, get_config_module, get_clouds, get_sizes, \
        get_cloud

@patch('gonzo.config.imp')
@patch('gonzo.config.os')
def test_get_config_module(os, imp):
    CONFIG = {'config': True}
    os.path.exists.return_value = True
    imp.find_module.return_value = Mock(), Mock(), Mock()
    imp.load_module.return_value = CONFIG

    assert get_config_module() == CONFIG


@patch('gonzo.config.get_config_module')
def test_get_clouds(cm):
    clouds = {'cloud': []}
    CONFIG = Mock(CLOUDS=clouds)
    cm.return_value = CONFIG

    assert get_clouds() == clouds 


@patch('gonzo.config.get_config_module')
def test_get_sizes(cm):
    sizes = Mock(name='sizes')
    CONFIG = Mock(SIZES=sizes)
    cm.return_value = CONFIG

    assert get_sizes() == sizes 


@patch('gonzo.config.git')
def test_get_reader(git):
    reader, repo = Mock(), Mock()
    repo.config_reader.return_value = reader
    git.Repo.return_value = repo

    assert get_reader() == reader


@patch('gonzo.config.get_reader')
def test_get_option(get_reader):
    # ensure we are calling get_value
    reader = Mock()
    get_reader.return_value = reader

    get_option('projectkey')

    assert len(reader.mock_calls) == 1
    assert reader.get_value.called


@patch('gonzo.config.git')
def test_get_writer(git):
    writer, repo = Mock(), Mock()
    repo.config_writer.return_value = writer
    git.Repo.return_value = repo

    assert get_writer('global') == writer


@patch('gonzo.config.get_writer')
def test_set_option(get_writer):
    # ensure that we are calling 'set_value' on a writer object
    writer = Mock()
    get_writer.return_value = writer

    set_option('projectkey', 'projectvalue')

    assert len(writer.mock_calls) == 1
    assert writer.set_value.called


@patch('gonzo.config.get_clouds')
@patch('gonzo.config.get_option')
def test_get_cloud(get_option, get_clouds):
	get_option = Mock(lambda x: 'thisisacloud')
	get_clouds = Mock(lambda x: {'thisisacloud': True})

	assert get_cloud()


