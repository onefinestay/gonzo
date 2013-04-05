""" Define your cloud connections.

Currently supports Openstack or AWS based clouds. Specify each backend you
use, and matching authentication details.
"""

CLOUDS = {
    'default': {
        ### For Openstack based clouds
        'BACKEND': 'gonzo.backends.openstack',

        # Openstack authentication details
        'TENANT_NAME': 'service',
        'USERNAME': '',
        'PASSWORD': '',
        'AUTH_URL': "http://cloud-host.example.com:5000/v2.0/",

        ### For AWS based clouds
        'BACKEND': 'gonzo.backends.aws',

        # AWS authentication details
        'AWS_USER_ID': 0,
        'AWS_ACCESS_KEY_ID': '',
        'AWS_SECRET_ACCESS_KEY': '',

        ### Common to either clouds backend
        # Glance or AMI image name
        'IMAGE_NAME': 'Ubuntu 12.04 cloudimg amd64',
        
        # Regions to deploy to, new instances will be evenly distributed
        'REGIONS': ['RegionOne',],

        # Key to be injected into new instances
        'KEY_NAME': 'master',
        'SSH_IDENTITY_PATH': "~/path/to/keys/master.pem",

        # Access to Route53 for recording hostnames and counting server types
        'AWS_ACCESS_KEY_ID': '',
        'AWS_SECRET_ACCESS_KEY': '',

        # domain to hold host information
        'INT_DNS_ZONE': 'example.com',
    },
}

""" Define the size of each server type you want to deploy

``default`` is required. Server types listed will use the specified instance
sizes. The list of server types will also be used for bash completion.
"""

SIZES = {
    'default': 'm1.small',
    'ecommerce-web': 'm1.large',
}