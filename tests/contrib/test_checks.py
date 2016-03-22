from io import StringIO
import sys

from mock import patch

from gonzo.contrib import checks


class TestAssertReleaseBranch(object):
    def setup_method(self, method):
        self.stderr = StringIO()

    def teardown_method(self, method):
        self.stderr.close()

    def _callFUT(self, *args, **kwargs):
        with patch('gonzo.contrib.checks.continue_check'):
            return checks.assert_release_branch(*args, **kwargs)

    @patch('gonzo.contrib.checks.get_current_branch')
    def test_not_release_branch(self, get_current_branch):
        get_current_branch.return_value = 'not-master'

        with patch.object(sys, 'stderr', self.stderr):
            self._callFUT(release_branch='master')

        output = self.stderr.getvalue()
        expected_warning = checks.ASSERT_RELEASE_BRANCH_WARNING
        expected_warning = expected_warning.format('master', 'not-master')
        assert expected_warning in output

    @patch('gonzo.contrib.checks.get_current_branch')
    def test_is_release_branch(self, get_current_branch):
        get_current_branch.return_value = 'master'

        with patch.object(sys, 'stderr', self.stderr):
            self._callFUT(release_branch='master')

        output = self.stderr.getvalue()
        assert output == ''


class TestAssertAheadOfCurrentRelease(object):
    def setup_method(self, method):
        self.stderr = StringIO()

    def teardown_method(self, method):
        self.stderr.close()

    def _callFUT(self, *args, **kwargs):
        with patch('gonzo.contrib.checks.continue_check'):
            return checks.assert_ahead_of_current_release(*args, **kwargs)

    @patch('gonzo.contrib.checks.diff_branch')
    def test_upstream_changes(self, diff_branch):
        diff_branch.return_value = (1, 0)  # (upstream, local)

        with patch.object(sys, 'stderr', self.stderr):
            self._callFUT(current_release='origin/master')

        output = self.stderr.getvalue()
        expected_warning = checks.ASSERT_AHEAD_OF_CURRENT_RELEASE_WARNING
        expected_warning = expected_warning.format(
            'origin/master')
        assert expected_warning in output

    @patch('gonzo.contrib.checks.diff_branch')
    def test_upstream_and_local_changes(self, diff_branch):
        diff_branch.return_value = (1, 1)  # (upstream, local)

        with patch.object(sys, 'stderr', self.stderr):
            self._callFUT(current_release='origin/master')

        output = self.stderr.getvalue()
        expected_warning = checks.ASSERT_AHEAD_OF_CURRENT_RELEASE_WARNING
        expected_warning = expected_warning.format(
            'origin/master')
        assert expected_warning in output

    @patch('gonzo.contrib.checks.diff_branch')
    def test_no_changes(self, diff_branch):
        diff_branch.return_value = (0, 0)  # (upstream, local)

        with patch.object(sys, 'stderr', self.stderr):
            self._callFUT(current_release='origin/master')

        output = self.stderr.getvalue()
        assert output == ''

    @patch('gonzo.contrib.checks.diff_branch')
    def test_local_changes(self, diff_branch):
        diff_branch.return_value = (0, 1)  # (upstream, local)

        with patch.object(sys, 'stderr', self.stderr):
            self._callFUT(current_release='origin/master')

        output = self.stderr.getvalue()
        assert output == ''
