from __future__ import absolute_import
import argparse
import functools

from gcalcli.printer import valid_color_name

COLOR_BASE_OPTS = {"type": valid_color_name,
                   "help": argparse.SUPPRESS
                   }

COLOR_PARSER_OPTIONS = {
    "--color_owner": {"default": "cyan"},
    "--color_writer": {"default": "cyan"},
    "--color_reader": {"default": "magenta"},
    "--color_freebusy": {"default": "default"},
    "--color_date": {"default": "yellow"},
    "--color_now-marker": {"default": "brightred"},
    "--color_border": {"default": "white"},
    "--color_title": {"default": "brightyellow"},
}


def parser_allow_deprecated(getter_func):
    if getter_func.__name__ == "get_color_parser":
        @functools.wraps(getter_func)
        def wrapped(*args, **kwargs):
            color_parser = getter_func()
            for opt in COLOR_PARSER_OPTIONS.items():
                color_parser.add_argument(
                    opt[0], default=opt[1]['default'], **COLOR_BASE_OPTS
                )
            return color_parser
        return wrapped
    if getter_func.__name__ == "get_remind_parser":
        def wrapped(*args, **kwargs):
            remind_parser = getter_func()
            remind_parser.add_argument(
                    "--default_reminders", action="store_true",
                    dest="default_reminders", default=False,
                    help=argparse.SUPPRESS)
            return remind_parser
        return wrapped


ALL_DEPRECATED_OPTS = COLOR_PARSER_OPTIONS
