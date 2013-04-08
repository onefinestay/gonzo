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

    if (use_color == 'always' or
            (use_color == 'auto' and sys.stdout.isatty())):
        return "%s%s%s" % (colour, msg, reset)
    else:
        return msg
