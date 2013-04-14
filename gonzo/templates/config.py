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
        'AWS_ACCESS_KEY_ID': '',
        'AWS_SECRET_ACCESS_KEY': '',

        ### Common to either clouds backend
        # Glance or AMI image name
        'IMAGE_NAME': 'Ubuntu 12.04 cloudimg amd64',

        # Regions to deploy to, new instances will be evenly distributed
        'REGIONS': ['RegionOne', ],

        # Key to be injected into new instances by the cloud provider
        # You typically upload the public key to the provide and give it a
        # name for internal reference
        'PUBLIC_KEY_NAME': 'master',
        'PRIVATE_KEY_FILE': "~/.ssh/id_rsa",

        # Access to Route53 for recording hostnames and counting server types
        # This is currently required even for Openstack based clouds; if you
        # are using AWS, you will have already specified these above
        'AWS_ACCESS_KEY_ID': '',
        'AWS_SECRET_ACCESS_KEY': '',

        # domain to hold host information
        'DNS_ZONE': 'example.com',
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
