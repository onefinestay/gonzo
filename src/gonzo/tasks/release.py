import os
import re
import gzip

from fabric.api import task, require, env, sudo, put, run
from fabric.contrib.files import exists, append
import git

from tasks import apache, instance
import settings as gonzo_settings

NEXT, PREVIOUS = 1, -1
DEFAULT_ARCHIVE_DIR = "./release_cache"


def get_adjacent_release(project_root, project, current_release,
                         direction=NEXT):
    """ Return next or previous release from the history file according to
        direction which is NEXT (1) or PREVIOUS (-1).

        If current_release is None then pick first or last entry if
        PREVIOUS / NEXT
    """

    history_path = os.path.join(project_root, project, 'releases/.history')
    if not exists(history_path):
        raise Exception("No history!")

    releases = run('cat {}'.format(history_path))
    releases = [l.strip() for l in releases.splitlines()]

    new_release = None
    if not current_release:
        try:
            new_release = releases[-1] if direction == NEXT else releases[0]
        except IndexError:
            new_release = None
    else:
        try:
            current_index = releases.index(current_release)
            next_index = current_index + direction
            if next_index < 0:
                new_release = None
            else:
                new_release = releases[next_index]
        except ValueError:
            # raised if the current release is not found
            new_release = None
        except IndexError:
            # reaised if the adjacent index is out of range
            new_release = None

    return new_release


def get_repo():
    """ Return a git.Repo object, caching it if not already in cache. """
    if not getattr(get_repo, "repo", None):
        cwd = os.getcwd()
        get_repo.repo = git.Repo(cwd)

    return get_repo.repo


def get_archive_name(commit_id, project, cache_dir=DEFAULT_ARCHIVE_DIR):
    """ Utility method to return fully qualified path to a cache file """

    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)

    proj_cache_dir = "%s/%s" % (cache_dir, project)
    cache_dir = os.path.realpath(proj_cache_dir)
    if not os.path.exists(proj_cache_dir):
        os.mkdir(proj_cache_dir)

    if not os.path.isdir(proj_cache_dir):
        raise Exception("Cache dir specified is not a directory!")

    return os.path.join(proj_cache_dir, "%s.tgz" % commit_id)


def create_archive(project, commit_id, cache_dir=DEFAULT_ARCHIVE_DIR):
    """ Create a tgz archive from the specified commit ID in the named project.
        Output file is in cache_dir which defaults to release_cache under the
        current working directory - it is created if it does not exist. File
        name is <commit_id>.tgz

        Returns (tarfile path, False) if the archive already exists;
        (tarfile path, True) if it is created.
    """

    tarfile = get_archive_name(commit_id, project, cache_dir)
    if os.path.isfile(tarfile):
        return (tarfile, False)

    _git = get_repo().git
    try:
        # the prefix used on the remote server for releases to live
        prefix = '/srv/{0}/releases/{1}/{0}/'.format(project, commit_id)
        with gzip.open(tarfile, "wb") as outfile:
            outfile.write(_git.archive(commit_id, format="tar", prefix=prefix))
    except git.exc.GitCommandError:
        os.remove(tarfile)
        raise Exception("Invalid commit ID: %s " % commit_id)

    return (tarfile, True)


def set_history(project_root, project, release):
    """ Append the release to the .history file unless it already exists in
        there.
    """
    history_path = os.path.join(project_root, project, 'releases/.history')
    # this fabric command does what we want here
    append(history_path, '{}\n'.format(release), use_sudo=True)


def register_release(project_root, project, release, chown_dirs='www-data'):
    """ Registers a newly pushed release by setting permissions and recording
        the release in the history file. To make active, a rollforward is
        needed subsequently.
    """
    target_release = os.path.join(project_root, project, "releases", release)

    if not os.path.exists(target_release):
        raise Exception("Target release %s not found" % target_release)

    if chown_dirs:
        sudo("chown -R {} {}".format(chown_dirs, target_release))

    set_history(project_root, project, release)


def get_active_branch(project):
    """ Return active branch for the specified repo """
    return get_repo(project).active_branch.name


def last_commit(project, branch=None):
    """ Return the last commit ID for the named branch, or the currently active
        branch if not specified
    """

    if not branch:
        branch = get_active_branch(project)

    return commit_by_name(project, branch)


def commit_by_name(project, name):
    """ Will check to see if name is a branch, and if so return the last commit
        ID on that branch, or if a commit ID in which case will return the full
        commit ID. If neither, raises exception.
    """
    repo = get_repo(project)

    try:
        commit = repo.commit(name)
        return commit.hexsha
    except git.BadObject:
        raise Exception("Invalid name: %s " % name)


@task
def set_project(project="onefinestay"):
    env.project = project


@task
def set_release(name=None):
    """ Finds the commit ID mapping to 'name' which can be a branch name, a
        commit ID or None in which case it defaults to HEAD. Sets env.commit
        which is used by, amongst others, push_release.
    """
    require("project", provided_by=["set_project"])
    if name:
        env.commit = commit_by_name(env.project, name)
    else:
        env.commit = last_commit(env.project)


@task
def current(project_root='/srv'):
    """ Return release ID (SHA) of the current release for the project """
    current = os.path.join(project_root, env.project, "releases", "current")

    current_release = run('readlink {}'.format(current))
    current_release_id = os.path.split(current_release)[-1]

    return current_release_id


@task
def push_release():
    """ Deploy commit identified by set_release previously.
        The release is not set live - the 'current' point is not amended -
        until a rollforward is done. The latter is a fast operation whilst this
        is slow.
    """
    require("commit", provided_by=["set_release"])
    require("project", provided_by=["set_project"])
    zipfile, _ = create_archive(env.project, env.commit)
    zfname = os.path.split(zipfile)[-1]

    # based on whether the archive is on the remote system or not, push our
    # archive
    target_file = "/srv/%s/packages/%s" % (env.project, zfname)
    if not exists(target_file):
        sudo("mkdir -p /srv/%s/packages/" % env.project)
        put(zipfile, target_file, use_sudo=True)
        sudo("cd /; tar zxf %s" % target_file)

    activate_command = ('cd /srv/%s/; source bin/activate; '
                        'cd releases/%s/%s'.format(env.project, env.commit))
    register_release(project_root='/srv',
                     project=env.project,
                     release=env.commit)

    if getattr(env, "install_requirements", True):
        if getattr(env, "pip_upgrade", False):
            upgrade_flag = "--upgrade"
        else:
            upgrade_flag = ""

        if getattr(env, "pip_quiet", False):
            quiet_flag = "--quiet"
        else:
            quiet_flag = ""
        sudo("%s ; pip install %s -r requirements.txt %s" %
            (activate_command, upgrade_flag, quiet_flag))

