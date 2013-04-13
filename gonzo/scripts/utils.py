import sys


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
