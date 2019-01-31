from __future__ import absolute_import
import argparse
import functools

from gcalcli.printer import valid_color_name


BASE_OPTS = {'color': {"type": valid_color_name,
                       "help": argparse.SUPPRESS},
             'remind': {}}

OPTIONS = {
    'color': {
        "--color_owner": {"default": "cyan"},
        "--color_writer": {"default": "cyan"},
        "--color_reader": {"default": "magenta"},
        "--color_freebusy": {"default": "default"},
        "--color_date": {"default": "yellow"},
        "--color_now-marker": {"default": "brightred"},
        "--color_border": {"default": "white"},
        "--color_title": {"default": "brightyellow"},
    },
    'remind': {
        "--default_reminders": {"action": "store_true",
                                "default": False}
    }
}


def parser_allow_deprecated(getter_func=None, name=None):
    if callable(getter_func):
        @functools.wraps(getter_func)
        def wrapped(*args, **kwargs):
            parser = getter_func()
            for opt in OPTIONS[name].items():
                parser.add_argument(
                    opt[0], default=opt[1]['default'], **BASE_OPTS[name]
                )
            return parser
        return wrapped

    else:
        def partial_parser_allow_deprecated(getter_func):
            return parser_allow_deprecated(getter_func, name=name)
        return partial_parser_allow_deprecated


ALL_DEPRECATED_OPTS = OPTIONS['color']
