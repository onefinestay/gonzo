from mock import Mock, patch

from gonzo.scripts.stack.show import build_resources_table, build_outputs_table


@patch('gonzo.scripts.stack.list_.colorize')
def test_resources_table(colorize):
    colorize.return_result = 'fancy-cloud'

    stack = Mock(resources=[
        Mock(logical_resource_id='logid', physical_resource_id='physid',
             resource_type='type', running_status='running'),
        Mock(logical_resource_id='logid2', physical_resource_id='physid2',
             resource_type='type2', running_status='stopped'),
    ])

    table = build_resources_table(stack, colorize)

    assert len(table._rows) == 2


@patch('gonzo.scripts.stack.list_.colorize')
def test_outputs_table(colorize):
    colorize.return_result = 'fancy-cloud'

    stack = Mock(outputs=[
        Mock(key='outputkey', value=123124, description='number'),
        Mock(key='anotheroutputkey', value='public_ip', description='string'),
        Mock(key='third_key', value='third_value', description='third')
    ])

    table = build_outputs_table(stack, colorize)

    assert len(table._rows) == 3
