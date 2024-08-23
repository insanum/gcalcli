import argparse
import sys

COLOR_NAMES = set(('default', 'black', 'red', 'green', 'yellow', 'blue',
                   'magenta', 'cyan', 'white', 'brightblack', 'brightred',
                   'brightgreen', 'brightyellow', 'brightblue',
                   'brightmagenta', 'brightcyan', 'brightwhite'))
ART_CHARS = {
    'fancy': {
        'hrz': '\033(0\x71\033(B',
        'vrt': '\033(0\x78\033(B',
        'lrc': '\033(0\x6A\033(B',
        'urc': '\033(0\x6B\033(B',
        'ulc': '\033(0\x6C\033(B',
        'llc': '\033(0\x6D\033(B',
        'crs': '\033(0\x6E\033(B',
        'lte': '\033(0\x74\033(B',
        'rte': '\033(0\x75\033(B',
        'bte': '\033(0\x76\033(B',
        'ute': '\033(0\x77\033(B'},
    'unicode': {
        'hrz': '\u2500',
        'vrt': '\u2502',
        'lrc': '\u2518',
        'urc': '\u2510',
        'ulc': '\u250c',
        'llc': '\u2514',
        'crs': '\u253c',
        'lte': '\u251c',
        'rte': '\u2524',
        'bte': '\u2534',
        'ute': '\u252c'},
    'ascii': {
        'hrz': '-',
        'vrt': '|',
        'lrc': '+',
        'urc': '+',
        'ulc': '+',
        'llc': '+',
        'crs': '+',
        'lte': '+',
        'rte': '+',
        'bte': '+',
        'ute': '+'}}


def valid_color_name(value):
    if value not in COLOR_NAMES:
        raise argparse.ArgumentTypeError(
            f'{value} is not a valid color. '
            f'Valid colours are: {", ".join(COLOR_NAMES)}')
    return value


class Printer(object):
    """Provide methods for terminal output with color (or not)"""

    def __init__(self, conky=False, use_color=True, art_style='ascii'):
        self.use_color = use_color
        self.conky = conky
        self.colors = {
                'default': '${color}' if conky else '\033[0m',
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
                None: '${color}' if conky else '\033[0m'}
        self.colorset = set(self.colors.keys())

        self.art_style = art_style
        self.art = ART_CHARS[self.art_style]

    def get_colorcode(self, colorname):
        return self.colors.get(colorname, '')

    def msg(self, msg, colorname='default', file=sys.stdout):
        if self.use_color:
            msg = self.colors[colorname] + msg + self.colors['default']
        file.write(msg)

    def err_msg(self, msg):
        self.msg(msg, 'brightred', file=sys.stderr)

    def debug_msg(self, msg):
        self.msg(msg, 'yellow', file=sys.stderr)

    def art_msg(self, arttag, colorname, file=sys.stdout):
        """Wrapper for easy emission of the calendar borders"""
        self.msg(self.art[arttag], colorname, file=file)
