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
from .dummy import DummyDNS
from .route53 import Route53DNS


_dns_service_register = {
    'dummy': DummyDNS,
    'route53': Route53DNS,
}


def get_dns_service():
    service_name = config.DNS.lower()
    service_cls = _dns_service_register[service_name]
    return service_cls()
