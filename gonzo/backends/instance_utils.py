def get_default_instance_tags_dict(environment, server_type, owner=None):
    """ Generate a tag dictionary suitable for identifying instance ownership
     and for identifying instances for gonzo releases.
    """
    default_tags = {
        'environment': environment,
        'server_type': server_type,
    }
    if owner:
        default_tags['owner'] = owner
    return default_tags


def add_default_security_groups(server_type, additional_security_groups=None):
    # Set defaults
    security_groups = [server_type, 'gonzo']

    # Add argument passed groups
    if additional_security_groups is not None:
        security_groups += additional_security_groups

    # Remove Duplicates
    security_groups = list(set(security_groups))

    return security_groups


def configure_instance(instance):
    instance.create_dns_entry()
