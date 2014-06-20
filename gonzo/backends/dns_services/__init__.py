"""DNS As A Service options

Add the following to the config for a Cloud ::

    {
        'BACKEND': 'gonzo.backends.example',
        ..

        'DNS_ZONE': 'localhost',
        'DNS_SERVICE': 'dummy',

        ..
    }

"""
from gonzo.config import config_proxy as config
from gonzo.exceptions import ConfigurationError
from .dummy import DummyDNS
from .route53 import Route53DNS


_dns_service_register = {
    'dummy': DummyDNS,
    'route53': Route53DNS,
}


def get_dns_service():
    cloud = config.CLOUD
    dns_service_name = cloud.get('DNS_SERVICE')

    if not dns_service_name in _dns_service_register:
        raise ConfigurationError(
            'Gonzo must be configured with a ``DNS_SERVICE``. This should be '
            'selected from: {}. For example, if you have no need for DNS add ' 
            '``DNS_SERVICE="dummy" to your config.py.'.format(
                ', '.join(_dns_service_register.keys())
            )
        )

    service_cls = _dns_service_register[dns_service_name]
    return service_cls()
