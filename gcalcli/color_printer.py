import sys
COLOR_NAMES = set(('default', 'black', 'red', 'green', 'yellow', 'blue',
                   'magenta', 'cyan', 'white', 'brightblack', 'brightred',
                   'brightgreen', 'brightyellow', 'brightblue',
                   'brightmagenta', 'brightcyan', 'brightwhite'))


def valid_color_name(value):
    if not value in COLOR_NAMES:
        raise argparse.ArgumentTypeError("%s is not a valid color" % value)
    return value


class ColorPrinter(object):
    """Provide methods for terminal output with color (or not)"""

    def __init__(self, conky=False, use_color=True):
        self.use_color = use_color
        self.colors = {
                'default': '' if conky else '\033[0m',
                'black': '${color black}' if conky else '\033[0;30m',
                'brightblack': '${color black}' if conky else '\033[30;1m',
                'red': '${color red}' if conky else '\033[0;31m',
                'brightred': '${color red}' if conky else '\033[31;1m',
                'green': '${color green}' if conky else '\033[0;32m',
                'brightgreen': '${color green}' if conky else '\033[32;1m',
                'yellow': '${color yellow}' if conky else '\033[0;33m',
                'brightyellow': '${color yellow}' if conky else '\033[33;1m',
                'blue': '${color blue}' if conky else '\033[0;34m',
                'brightblue': '${color blue}' if conky else '\033[34;1m',
                'magenta': '${color magenta}' if conky else '\033[0;35m',
                'brightmagenta': '${color magenta}' if conky else '\033[35;1m',
                'cyan': '${color cyan}' if conky else '\033[0;36m',
                'brightcyan': '${color cyan}' if conky else '\033[36;1m',
                'white': '${color white}' if conky else '\033[0;37m',
                'brightwhite': '${color white}' if conky else '\033[37;1m',
                 None: '' if conky else '\033[0m'}

    def msg(self, msg, colorname, file=sys.stdout):
        if self.use_color:
            msg = self.colors[colorname] + msg + self.colors['default']
        file.write(msg)

    def err_msg(self, msg):
        self.msg(msg, 'brightred', file=sys.stderr)

    def debug_msg(self, msg):
        self.msg(msg, 'yellow', file=sys.stderr)
