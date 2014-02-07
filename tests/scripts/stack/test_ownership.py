import json
from gonzo.backends import insert_stack_owner_output


def test_ownership():

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

    template = insert_stack_owner_output(template=template,
                                         owner="test-user")
    json_template = json.loads(template)

    resources = json_template.get("Resources", None)
    outputs = json_template.get("Outputs", None)

    assert resources is not None
    assert outputs is not None

    assert resources.get("existing_resource", None) is not None

    existing_output = outputs.get("existing_output", None)
    assert existing_output is not None
    assert existing_output["Value"] == "existing value"

    owner_output = outputs.get("owner", None)
    assert owner_output is not None
    assert owner_output["Value"] == "test-user"
