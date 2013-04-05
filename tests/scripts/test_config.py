import StringIO
import tempfile
from mock import Mock, MagicMock, patch
from git.config import GitConfigParser

from gonzo.config import set_option, get_option
from gonzo.scripts.config import set_cloud, get_cloud


@patch('gonzo.config.git')
def test_set_option(git):
	# our .git_config
	f = StringIO.StringIO()
	f.name = "foo"
	config_writer = GitConfigParser(f, False)
	repo = Mock(config_writer=lambda: config_writer)
	git.Repo.return_value = repo

	set_option('projectkey', 'projectvalue')

	assert config_writer.sections() == ['gonzo']
	assert config_writer.options('gonzo') == ['projectkey']
	assert config_writer.get_value('gonzo', 'projectkey') == 'projectvalue'

	f.seek(0)
	assert 'gonzo' and 'projectkey' and 'projectvalue' in f.read()


@patch('gonzo.config.git')
def test_get_option(git):
	# our .git_config
	f = StringIO.StringIO()
	f.name = "bar"

	# before we can test get_option we must set an option
	config_writer = GitConfigParser(f, False)
	config_writer.set_value('gonzo', 'projectkey', 'projectvalue')
	# now do the test (writer and reader are both instances of GitConfigParser)
	f.seek(0) # this would be executed if we were using the full mechanics

	config_reader = GitConfigParser([f], read_only=True)

	repo = Mock(config_reader=lambda: config_reader)
	git.Repo.return_value = repo

	assert get_option('projectkey') == 'projectvalue'

