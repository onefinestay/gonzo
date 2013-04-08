"""
gonzo
=====

"""


try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('gonzo').version
except:
    VERSION = 'unknown'
