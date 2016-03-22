import os
from urllib.parse import urlparse

from jinja2 import Environment
import requests

from gonzo.config import config_proxy as config
from gonzo.exceptions import DataError


def get_parsed_document(entity_name, uri=None, config_params_key=None,
             additional_params=None):
    """ Fetch a document from uri specified by `uri` and parse as a template.
    Template parameters include cli, config and predefined dictionaries.
    Useful for building CloudFormation templates or UserData scripts.
    """
    user_data_params = build_params_dict(entity_name, config_params_key,
                                         additional_params)
    return get_document(uri, user_data_params)


def build_params_dict(entity_name, config_params_key, additional_params=None):
    """ Returns a dictionary of parameters to use when rendering CloudFormation
    templates or user data scripts from template.

    Parameter sources include gonzo defined defaults, cloud configuration and
    a comma separated key value command line argument. They get overridden in
    that order. """
    params = {
        'hostname': entity_name,
        'stackname': entity_name,
        'domain': config.get_cloud()['DNS_ZONE'],
        'fqdn': "%s.%s" % (entity_name, config.get_cloud()['DNS_ZONE']),
    }

    if config_params_key in config.get_cloud():
        params.update(config.get_cloud()[config_params_key])

    if additional_params is not None:
        params.update(additional_params)

    return params


def get_document(uri, params=None):
    """ Attempt to fetch user data from URL or file. And render, replacing
     parameters """

    if uri is None:
        raise ValueError("Document URI cannot be None")

    try:
        urlparse(uri)
        data = fetch_from_url(uri)
    except requests.exceptions.MissingSchema:
        # Not a url. possibly a file.
        uri = os.path.expanduser(uri)
        uri = os.path.abspath(uri)

        if os.path.isabs(uri):
            try:
                data = open(uri, 'r').read()
            except IOError as err:
                err_msg = "Failed to read from file: {}".format(err)
                raise DataError(err_msg)
        else:
            # Not url nor file.
            err_msg = "Unknown UserData source: {}".format(uri)
            raise DataError(err_msg)
    except requests.exceptions.ConnectionError as err:
        err_msg = "Failed to read from URL: {}".format(err)
        raise DataError(err_msg)

    data_tpl = Environment().from_string(data)
    return data_tpl.render(params)


def fetch_from_url(url):
    resp = requests.get(url)
    if resp.status_code != requests.codes.ok:
        raise requests.exceptions.ConnectionError("Bad response")

    return resp.text
