import json

from gonzo.config import config_proxy as config
from gonzo.helpers.document_loader import get_parsed_document
from gonzo.backends.instance_utils import get_default_instance_tags_dict


def generate_stack_template(stack_type, stack_name,
                            template_uri, template_params,
                            instance_resource_type, owner=None):
    template_uri = config.get_namespaced_cloud_config_value(
        'ORCHESTRATION_TEMPLATE_URIS', stack_type, override=template_uri)
    if template_uri is None:
        raise ValueError('A template must be specified by argument or '
                         'in config')

    template = get_parsed_document(stack_name, template_uri,
                                   'ORCHESTRATION_TEMPLATE_PARAMS',
                                   template_params)

    # Parse as json for validation and for injecting gonzo defaults
    template_dict = json.loads(template)

    if owner:
        template_dict = insert_stack_owner_output(template_dict, owner)

    template_dict = insert_stack_instance_tags(
        template_dict, instance_resource_type, stack_name, owner)

    return json.dumps(template_dict)


def insert_stack_owner_output(template_dict, owner):
    """ Adds a stack output to a template with key "owner" """
    template_outputs = template_dict.get('Outputs', {})
    template_outputs['owner'] = {
        'Value': owner,
        'Description': "This stack's launcher (Managed by Gonzo)"
    }
    template_dict.update({'Outputs': template_outputs})

    return template_dict


def insert_stack_instance_tags(template_dict, instance_resource_type,
                               environment, owner):
    """ Updates tags of each instance resource to include gonzo defaults
    """
    resources = template_dict.get('Resources', {})
    for resource_name, resource_details in resources.items():
        if resource_details['Type'] != instance_resource_type:
            # We only care about tagging instances
            continue

        # Ensure proper tag structure exists
        if 'Properties' not in resource_details:
            resource_details['Properties'] = {}
        if 'Tags' not in resource_details['Properties']:
            resource_details['Properties']['Tags'] = []

        existing_tags = resource_details['Properties']['Tags']
        default_tags = get_default_instance_tags_dict(
            environment, resource_name, owner)

        # Remove potential duplicates
        for existing_tag in existing_tags:
            if existing_tag['Key'] in default_tags.keys():
                existing_tags.remove(existing_tag)

        # Add defaults
        for key, value in default_tags.iteritems():
            existing_tags.append({'Key': key, 'Value': value})

    return template_dict
