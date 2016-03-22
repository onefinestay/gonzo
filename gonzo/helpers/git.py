from fabric.api import local
from fabric.context_managers import hide
from fabric.utils import puts


def get_current_branch():
    """ Uses git to return the current symbolic-ref (branch)
    """
    with hide('running', 'stdout'):
        branch = local('git symbolic-ref -q HEAD', capture=True)

    return branch.replace('refs/heads/', '')


def diff_branch(target_branch):
    """ Compares your current git HEAD to `target_branch` and returns a tuple
        of integers denoting how many commits ahead each branch is
        `(upstream_ahead, local_ahead)`
    """
    with hide('running', 'stdout'):
        puts('fetching upstream branches...')
        local('git fetch')
        rev_list = 'git rev-list --count --left-right {}...HEAD'.format(
            target_branch)
        upstream_counts = local(rev_list, capture=True)

    upstream_ahead, local_ahead = list(map(int, upstream_counts.split('\t')))
    return upstream_ahead, local_ahead
