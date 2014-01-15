""" Define your cloud connections.

Currently supports Openstack or AWS based clouds. Specify each backend you
use, and matching authentication details.
"""

CLOUDS = {
    'default': {
        ### For Openstack based clouds
        'BACKEND': 'gonzo.backends.openstack',
        ### For AWS based clouds
        #'BACKEND': 'gonzo.backends.aws',

        # Openstack authentication details
        'TENANT_NAME': 'service',
        'USERNAME': '',
        'PASSWORD': '',
        'AUTH_URL': "http://cloud-host.example.com:5000/v2.0/",

        # AWS authentication details
        #
        # Always required! When working with OpenStack, keys will be used for
        # for recording hostnames and counting server types with Route53.
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

        # domain to hold host information
        'DNS_ZONE': 'example.com',

        # Default cloud-init script to pass when creating new instances.
        # Can be overridden with --user-data.
        # Will be parsed as a template. See templates/userdata_template for
        # more info.
        'DEFAULT_USER_DATA': None,
        # Extra params to use when rendering user data template.
        'USER_DATA_PARAMS': {},

        # Default CloudFormation templates to use when launching stacks.
        # Can be overridden with --template
        # Will be parsed as a template.
        'ORCHESTRATION_TEMPLATE_URIS': {
            'default': 'https://s3...',
            'stack-name': 'https://s3...',
        },
        # Extra params to use when rendering CloudFormation template.
        'ORCHESTRATION_TEMPLATE_PARAMS': {
            'puppetmaster': 'puppetmaster.example.com',
        },

        # OpenStack only.
        'ORCHESTRATION_URL': 'http://heat-cfn-api.example.com/v1/',
        'ORCHESTRATION_CREDENTIALS': {
            'aws_access_key_id': '',
            'aws_secret_access_key': '',
        },
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
