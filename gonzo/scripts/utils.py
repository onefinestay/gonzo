import sys
from prettytable import PrettyTable


def colorize(msg, colour, use_color='auto'):
    colour_map = {
        'red': '\x1b[31m',
        'yellow': '\x1b[33m',
        'green': '\x1b[32m',
        'blue': '\x1b[34m',
    }

    reset = "\x1b[0m"
    colour = colour_map[colour]

    force_color = (use_color == 'always')
    auto_color = (use_color == 'auto')
    color_recommended = sys.stdout.isatty()

    if (force_color or (auto_color and color_recommended)):
        return "%s%s%s" % (colour, msg, reset)
    else:
        return msg


def print_table(row_definer, headers, objects, show_header=False,
                use_color='auto'):
    tableoutput = PrettyTable(headers)
    for column in headers:
        tableoutput.align[column] = "l"

    tableoutput.header = show_header
    tableoutput.sortby = "name"
    tableoutput.vertical_char = " "
    tableoutput.horizontal_char = " "

    tableoutput.junction_char = " "
    for object in objects:
        tableoutput.add_row(row_definer(object, use_color))

    print tableoutput.get_string()
