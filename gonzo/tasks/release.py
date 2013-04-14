from __future__ import absolute_import  # otherwise we find tasks.gonzo

import os

from fabric.api import task, env, sudo, put, run, local, settings
from fabric.contrib.files import exists, append

from gonzo.config import PROJECT_ROOT, local_state

NEXT, PREVIOUS = 1, -1
DEFAULT_ARCHIVE_DIR = "./release_cache"

# TODO: move some of these, e.g. get_adjacent_release (all non-tasks?)
# to a separate module


def get_project():
    """ Try to return the intended project name for this repository. Otherwise
        raise an acceptable error.

        1) it was specified on the command line
        2) it was specified in the git repo
    """
    project = getattr(env, 'project', local_state['project'])
    if project is None:
        raise Exception('No project specified. Cannot continue')
    return project


def get_commit():
    """ Try to return the intended commit / release to deal with. Otherwise
        raise an acceptable error.

        1) it was specified on the command line
        2) use the current branch in the target repo
    """
    commit = getattr(env, 'commit', last_commit())
    if commit is None:
        raise Exception(
            'Unable to ascertain target commit from command line or git repo')
    return commit


def project_path(*extra):
    return os.path.join(PROJECT_ROOT, get_project(), *extra)


def activate_command():
    project = get_project()
    commit = get_commit()
    return 'cd {}; source bin/activate; cd {}'.format(
        project_path(), project_path('releases', commit, project))


def get_releases():
    if not exists(project_path('releases', '.history')):
        raise Exception("No history!")

    releases = run('cat {}'.format(project_path('releases', '.history')))
    return [l.strip() for l in releases.splitlines()]


def get_adjacent_release(current_release, direction=NEXT):
    """ Return next or previous release from the history file according to
        direction which is NEXT (1) or PREVIOUS (-1).

        If current_release is None then pick first or last entry if
        PREVIOUS / NEXT
    """
    releases = get_releases()

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


def get_archive_name(commit_id, project, cache_dir=DEFAULT_ARCHIVE_DIR,
                     format='tgz'):
    """ Utility method to return fully qualified path to a cache file """

    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)

    proj_cache_dir = "%s/%s" % (cache_dir, project)
    cache_dir = os.path.realpath(proj_cache_dir)
    if not os.path.exists(proj_cache_dir):
        os.mkdir(proj_cache_dir)

    if not os.path.isdir(proj_cache_dir):
        raise Exception("Cache dir specified is not a directory!")

    return os.path.join(proj_cache_dir, "{}.{}".format(commit_id, format))


def create_archive(commit_id, cache_dir=DEFAULT_ARCHIVE_DIR, format='tgz'):
    """ Create a tgz archive from the specified commit ID in the named project.
        Output file is in cache_dir which defaults to release_cache under the
        current working directory - it is created if it does not exist. File
        name is <commit_id>.tgz

        Returns (tarfile path, False) if the archive already exists;
        (tarfile path, True) if it is created.
    """

    project = get_project()
    tarfile = get_archive_name(commit_id, project, cache_dir)
    prefix = project_path('releases', commit_id, project)
    if os.path.isfile(tarfile):
        return (tarfile, False)

    git_archive_template = 'git archive --format={0} --prefix={1} {2} > "{3}"'
    git_command = git_archive_template.format(
        format, prefix, commit_id, tarfile)

    with settings(warn_only=True):
        res = local(git_command, capture=True)

    if not res.succeeded:
        os.remove(tarfile)
        raise Exception("Invalid commit ID: %s " % commit_id)

    return (tarfile, True)


def set_history(release):
    """ Append the release to the .history file unless it already exists in
        there.
    """
    # this fabric command does what we want here
    history_path = project_path('releases', '.history')
    append(history_path, '{}\n'.format(release), use_sudo=True)


def register_release(release, chown_dirs='www-data'):
    """ Registers a newly pushed release by setting permissions and recording
        the release in the history file. To make active, a rollforward is
        needed subsequently.
    """
    target_release = project_path("releases", release)

    if not os.path.exists(target_release):
        raise Exception("Target release %s not found" % target_release)

    if chown_dirs:
        sudo("chown -R {} {}".format(chown_dirs, target_release))

    set_history(release)


def last_commit(branch=None):
    """ Return the last commit ID for the named branch, or the currently active
        branch if not specified
    """

    if not branch:
        branch = 'HEAD'

    return commit_by_name(branch)


def commit_by_name(name):
    """ Will check to see if name is a branch, and if so return the last commit
        ID on that branch, or if a commit ID in which case will return the full
        commit ID. If neither, raises exception.
    """
    with settings(warn_only=True):
        res = local('git rev-parse {}'.format(name), capture=True)

    if res.succeeded:
        return res
    else:
        raise Exception("Invalid name: %s " % name)


def purge_release(release):
    """ Purge package file for the particular release.

        Removes the cached file in ``project_root/project/packages`` and remove
        the untarred directory and remove history entry only if this is not the
        target of the 'current' pointer
    """
    package_name = project_path('packages', '%s.tgz' % release)
    released_dir = project_path('releases', release)
    history_path = project_path('releases', '.history')
    current_pointer = current()

    if exists(package_name):
        sudo('rm {}'.format(package_name))

    if current_pointer == release:
        raise Exception(
            "Cannot remove checked out directory as it is the current release")

    sudo('rm -rf {}'.format(released_dir))

    # remove history entry
    releases = get_releases()
    releases = [v for v in releases if v.strip()]
    sudo('cat << EOF > {}\n{}\nEOF'.format(history_path, '\n'.join(releases)))


def roll_history(direction=NEXT):
    """ Roll the current release back or forward to the adjacent one in the
        history file. if no current pointer exists, it is assumed that the last
        (most recent) entry in the history file is the one to link if rolling
        forward, and the first (earliest) entry is the one to link if rolling
        backwards.

        Rolling forward is the key step to make a release live after
        registering a release. Restarting any processes running the old code is
        also required.
    """
    FIRST_TIME = True
    current_release = current()

    if exists(current):
        FIRST_TIME = False
        current_release = current()
    else:
        current_release = None

    next_release = get_adjacent_release(current_release, direction)

    if not next_release:
        raise Exception("No release to which to roll %s" %
                        {PREVIOUS: "back", NEXT: "forward"}[direction])

    next_release = project_path("releases", next_release)
    if not FIRST_TIME:
        sudo('rm {}'.format(current_release))
    sudo('ln -s {0} {1}'.format(next_release, current_release))


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
    print current()


@task
def set_commit(name):
    """ Finds the commit ID mapping to 'name' which can be a branch name, a
        commit ID or None in which case it defaults to HEAD. Sets env.commit
        which is used by, amongst others, push_release.
    """
    env.commit = commit_by_name(name)


@task
def current():
    """ Return release ID (SHA) of the current release for the project """
    current_path = project_path("releases", "current")

    current_release = run('readlink {}'.format(current_path))
    current_release_id = os.path.split(current_release)[-1]

    return current_release_id


@task
def push():
    """ Deploy commit identified by set_commit previously.
        The release is not set live - the 'current' point is not amended -
        until a rollforward is done. The latter is a fast operation whilst this
        is slow.
    """
    commit = get_commit()
    zipfile, _ = create_archive(commit)
    zfname = os.path.split(zipfile)[-1]

    # based on whether the archive is on the remote system or not, push our
    # archive
    packages_dir = project_path('packages')
    target_file = project_path('packages', zfname)
    if not exists(target_file):
        sudo("mkdir -p {}".format(packages_dir))
        put(zipfile, target_file, use_sudo=True)
        sudo("cd /; tar zxf %s" % target_file)

    register_release(release=commit)

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
            (activate_command(), upgrade_flag, quiet_flag))


@task
def prune(releases='4'):
    """ Orders the project directory and then will keep the number of specified
        releases and delete any previous releases present to minimise the disk
        space.

        Arguments:

            releases (str): a string representation of the number of releases
                            to be left.
    """
    releases = int(releases)  # fabric params always come through as strings
    release_list = get_releases()
    current_release = current()
    index = release_list.index(current_release)
    if index > releases:
        delete_release_list = release_list[:index - releases]
        for release in delete_release_list:
            purge_release(release)


@task
def purge_local_package(package):
    """ Purge a pip installed package from a project virtualenv. """
    sudo("{0} ; yes y | pip uninstall {2}".format(activate_command(), package))


@task
def purge(release):
    """ USE WITH CARE! This removes:

            * the package file from local cache
            * the package file from the remote package cache
            * the unpacked directory will be removed as long as it is not the
              current release.
    """
    purge_release(release)


@task
def rollback():
    """ Roll back a release to the previous, if available """
    roll_history(PREVIOUS)


@task
def rollforward():
    """ Roll forward a release to a newer one, if available """
    roll_history(NEXT)
