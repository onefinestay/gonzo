from datetime import datetime
from mock import Mock, patch

from gonzo.scripts.stack.list_ import print_stack_summary


@patch('gonzo.scripts.stack.list_.colorize')
def test_print_stack(colorize):
    colorize.return_value = 'fancy-cloud'

    stack = Mock(
        name='name',
        description="description",
        status="status",
        owner='owner',
        uptime=datetime(2000, 01, 01),
    )

    expected = [
        'fancy-cloud',
        'description',
        'fancy-cloud',
        'owner',
        'fancy-cloud',
    ]
    result = print_stack_summary(stack)

    assert result == expected
