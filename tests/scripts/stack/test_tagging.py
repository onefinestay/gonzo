import json

from mock import patch

from gonzo.backends.template_utils import generate_stack_template


@patch("gonzo.backends.template_utils.get_default_instance_tags_dict")
@patch("gonzo.backends.template_utils.get_parsed_document")
def test_instance_tagging(get_parsed_doc, get_tags_dict):
    tags_dict = {
        "environment": "overwritten",
        "extra": "value",
    }
    get_tags_dict.return_value = tags_dict

    template = """
{
  "Resources" : {
    "decoy-resource": {
        "Type": "not-interesting-type",
        "Properties": {}
    },
    "no-other-tags": {
        "Type": "instance-type",
        "Properties": {}
    },
    "existing-tags": {
        "Type": "instance-type",
        "Properties": {
            "Tags": [
                {
                    "Key": "decoy",
                    "Value": "leave me be"
                },
                {
                    "Key": "environment",
                    "Value": "overwrite me"
                }
            ]
        }
    }
  }
}"""
    get_parsed_doc.return_value = template

    template = generate_stack_template(None, None, "template_uri", None,
                                       instance_resource_type="instance-type",
                                       owner="test-user")
    template_dict = json.loads(template)

    resources = template_dict.get("Resources", None)

    assert resources is not None

    decoy_resource = resources.get("decoy-resource", None)
    assert decoy_resource is not None
    assert decoy_resource['Properties'] == {}

    no_other_tags_resource = resources.get("no-other-tags", None)
    no_other_tags_tags = no_other_tags_resource['Properties']['Tags']
    for key, value in tags_dict.items():
        assert {'Key': key, 'Value': value} in no_other_tags_tags

    existing_tags_resource = resources.get("existing-tags", None)
    existing_tags_tags = existing_tags_resource['Properties']['Tags']
    for key, value in tags_dict.items():
        assert {'Key': key, 'Value': value} in existing_tags_tags
