from __future__ import absolute_import  # otherwise we find tasks.gonzo

import os

from fabric.api import task, env, sudo, put, run, local, settings
from fabric.context_managers import prefix as fab_prefix
from fabric.contrib.files import exists

from gonzo.config import PROJECT_ROOT, local_state
from gonzo.utils import last_index

DEFAULT_ARCHIVE_DIR = "./release_cache"
USER = 'www-data'  # TODO: make configurable


def usudo(*args, **kwargs):
    kwargs['user'] = USER
    return sudo(*args, **kwargs)


def get_project():
    """ Try to return the intended project name for this repository. Otherwise
        raise an acceptable error.

        1) it was specified on the command line
        2) it was specified in the git repo
    """
    project = getattr(env, 'project', local_state['project'])
    if project is None:
        raise RuntimeError('No project specified. Cannot continue')
    return project


def get_commit():
    """ Try to return the intended commit / release to deal with. Otherwise
        raise an acceptable error.

        1) it was specified on the command line
        2) use the current branch in the target repo
    """
    commit = getattr(env, 'commit', None) or rev_parse('HEAD')
    if commit is None:
        raise RuntimeError(
            'Unable to ascertain target commit from command line or git repo')
    return commit


def project_path(*extra):
    return os.path.join(PROJECT_ROOT, get_project(), *extra)


def activate_command():
    project = get_project()
    commit = get_commit()
    return 'cd {}; source bin/activate; cd {}'.format(
        project_path(), project_path('releases', commit, project))


def list_releases():
    if not exists(project_path('releases', '.history')):
        return []

    releases = run('cat {}'.format(project_path('releases', '.history')))
    return [l.strip() for l in releases.splitlines()]


def get_previous_release(current_release):
    """ Return the previously active release from the history file """
    releases = list_releases()

    try:
        current_index = last_index(releases, current_release)
        previous_index = current_index - 1
        if previous_index < 0:
            return None
        else:
            return releases[previous_index]
    except ValueError:
        # raised if the current release is not found
        return None


def get_archive_name(commit_id, project, cache_dir=DEFAULT_ARCHIVE_DIR,
                     format='tgz'):
    """ Utility method to return fully qualified path to a cache file """

    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)

    proj_cache_dir = os.path.join(cache_dir, project)
    cache_dir = os.path.realpath(proj_cache_dir)
    if not os.path.exists(proj_cache_dir):
        os.mkdir(proj_cache_dir)

    if not os.path.isdir(proj_cache_dir):
        raise RuntimeError("Cache dir specified is not a directory!")

    return os.path.join(proj_cache_dir, "{}.{}".format(commit_id, format))


def create_archive(commit_id, cache_dir=DEFAULT_ARCHIVE_DIR,
        file_format='tgz'):
    """ Create a tgz archive from the specified commit ID in the named project.
        Output file is in cache_dir which defaults to release_cache under the
        current working directory - it is created if it does not exist. File
        name is <commit_id>.tgz

        Returns (tarfile path, False) if the archive already exists;
        (tarfile path, True) if it is created.
    """

    project = get_project()
    tarfile = get_archive_name(commit_id, project, cache_dir)
    prefix = project_path('releases', commit_id, project, '')  # end with sep
    if os.path.isfile(tarfile):
        return (tarfile, False)

    git_archive_template = 'git archive --format={0} --prefix={1} {2} > "{3}"'
    git_command = git_archive_template.format(
        file_format, prefix, commit_id, tarfile)

    with settings(warn_only=True):
        res = local(git_command, capture=True)

    if not res.succeeded:
        os.remove(tarfile)
        raise RuntimeError("Invalid commit ID: {} " .format(commit_id))

    return (tarfile, True)


def _append_to_history(release):
    history_path = project_path('releases', '.history')
    usudo('echo {} >> {}'.format(release, history_path))


def append_to_history(release):
    """ Append the release to the .history file

        If ``release`` is already the last entry, do nothing.
    """

    releases = list_releases()
    try:
        current = releases[-1]
    except IndexError:
        current = None

    if release == current:
        return

    _append_to_history(release)


def rollback_history():
    """ Remove the last line from the .history file """
    history_path = project_path('releases', '.history')
    if exists(history_path):
        usudo("sed -i '$ d' {}".format(history_path))


def rev_parse(revision):
    """ Use git rev-parse to parse ``revision`` into a commit sha """

    with settings(warn_only=True):
        res = local('git rev-parse {}'.format(revision), capture=True)

    if res.succeeded:
        return res
    else:
        raise RuntimeError("Unknown revision: {}".format(revision))


def _replace_history(release_list):
    history_path = project_path('releases', '.history')
    usudo('cat << EOF > {}\n{}\nEOF'.format(
        history_path, '\n'.join(release_list)))


@task
def set_project(project):
    env.project = project


@task
def show_history(full=False):
    """ Cat the release history on remote hosts for the specified project. """
    history_path = project_path('releases', '.history')
    if full:
        run("cat {}".format(history_path))
    else:
        run("tail -n 3 {}".format(history_path))
    print get_current()


@task
def set_commit(revision):
    """ Set env.commit which is used by, amongst others, push_release.

        ``revision`` may be anything git can parse into a commit sha
    """
    env.commit = rev_parse(revision)


@task
def get_current():
    """ Return release ID (SHA) of the current release for the project

        If no ``current`` symlink exists, return ``None``
    """

    current_path = project_path("releases", "current")

    with settings(warn_only=True):
        current_release = run('readlink {}'.format(current_path))

    if not current_release.succeeded:
        return None

    current_release_id = os.path.split(current_release)[-1]

    return current_release_id


def set_current(release):
    release_dir = project_path("releases", release)
    symlink = project_path("releases", "current")

    usudo('rm {}'.format(symlink))
    usudo('ln -s {} {}'.format(release_dir, symlink))


@task
def push():
    """ Deploy commit identified by ``set_commit`` previously.
        The release is not set live - the 'current' point is not amended -
        until ``activate`` is invoked. The latter is a fast operation whilst
        this is slow.
    """
    commit = get_commit()
    zipfile, _ = create_archive(commit)
    zfname = os.path.split(zipfile)[-1]

    # based on whether the archive is on the remote system or not, push our
    # archive
    packages_dir = project_path('packages')
    target_file = project_path('packages', zfname)

    base_dir = project_path()

    if not exists(project_path('bin', 'activate')):
        with settings(warn_only=True):
            res = sudo("virtualenv {}".format(base_dir))

        # TODO: install setuptools and virtualenv? or bootatrap, e.g.
        # http://eli.thegreenplace.net/2013/04/20/bootstrapping-virtualenv/
        if not res.succeeded:
            if "virtualenv: command not found" in res:
                raise RuntimeError(
                    "Virtualenv not installed on target server!")
            else:
                raise RuntimeError(res)

    sudo("chown -R {} {}".format(USER, base_dir))

    if not exists(target_file):
        usudo("mkdir -p {}".format(packages_dir))

        # can't pass a user to 'put'
        put(zipfile, target_file, use_sudo=True)
        sudo("chown -R {} {}".format(USER, target_file))

        usudo("cd /; tar zxf {}".format(target_file))

    if getattr(env, "install_requirements", True):
        if getattr(env, "pip_upgrade", False):
            upgrade_flag = "--upgrade"
        else:
            upgrade_flag = ""

        if getattr(env, "pip_quiet", False):
            quiet_flag = "--quiet"
        else:
            quiet_flag = ""
        with fab_prefix(activate_command()):
            usudo("pip install {} -r requirements.txt {}".format(
                upgrade_flag, quiet_flag))


@task
def prune(keep='4'):
    """ Orders the project directory and then will keep the number of specified
        releases and delete any previous releases present to minimise the disk
        space.

        Arguments:

            keep (str): a string representation of the number of releases
                            to be left.
    """
    keep = int(keep)  # fabric params always come through as strings
    release_list = list_releases()
    current_release = get_current()
    index = release_list.index(current_release)
    if index > keep:
        delete_release_list = release_list[:index - keep]
        for release in delete_release_list:
            purge_release(release)


@task
def purge_local_package(package):
    """ Purge a pip installed package from a project virtualenv. """
    with fab_prefix(activate_command()):
        usudo("pip uninstall --yes {}".format(package))


@task
def purge_release(release):
    """ Remove all data related to the release.

    This removes:

        - the package file from local cache
        - the package file from the remote package cache
        - the unpacked directory will be removed as long as it is not the
              current release.
    """
    package_name = project_path('packages', '{}.tgz'.format(release))
    released_dir = project_path('releases', release)
    current_pointer = get_current()

    if exists(package_name):
        usudo('rm {}'.format(package_name))

    if current_pointer == release:
        raise RuntimeError(
            "Cannot remove checked out directory as it is the current release")

    usudo('rm -rf {}'.format(released_dir))

    # remove history entry
    releases = list_releases()
    releases = [v for v in releases if v != release]
    _replace_history(releases)





@task
def rollback():
    """ Roll back to the most recent active release in the history file.

        This is used for quick recovery in case of bugs discovered shortly
        after activating a new release.

        Like ``activate``, this only moves a symlink, so any process using the
        code should be restarted following this command.
    """

    current_release = get_current()

    previous_release = get_previous_release(current_release)

    if not previous_release:
        raise RuntimeError("No release to roll back to")

    # sadly, there's not way to make this atomic
    set_current(previous_release)
    rollback_history()


@task
def activate():
    """ Activate the release specified by ``set_commit``, if available.

        Note that this command only moves a symlink, so any process using the
        code should be restarted following this command.
    """
    commit = get_commit()
    # sadly, there's not way to make this atomic
    set_current(commit)
    append_to_history(commit)
