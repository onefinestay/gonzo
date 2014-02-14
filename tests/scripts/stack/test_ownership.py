import json
from mock import patch
from gonzo.backends import generate_stack_template


@patch("gonzo.backends.get_parsed_document")
def test_ownership(get_parsed_doc):

    template = """
{
  "Resources" : {
    "existing_resource": {}
  },

  "Outputs" : {
    "existing_output" : {
      "Value": "existing value",
      "Description" : "existing description"
    }
  }
}"""
    get_parsed_doc.return_value = template

    template = generate_stack_template(None, None, "template_uri", None,
                                       owner="test-user")
    template_dict = json.loads(template)

    resources = template_dict.get("Resources", None)
    outputs = template_dict.get("Outputs", None)

    assert resources is not None
    assert outputs is not None

    assert resources.get("existing_resource", None) is not None

    existing_output = outputs.get("existing_output", None)
    assert existing_output is not None
    assert existing_output["Value"] == "existing value"

    owner_output = outputs.get("owner", None)
    assert owner_output is not None
    assert owner_output["Value"] == "test-user"
