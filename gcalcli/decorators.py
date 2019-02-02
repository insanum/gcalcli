from __future__ import absolute_import
import argparse
import functools

import gcalcli
from gcalcli.printer import valid_color_name


BASE_OPTS = {'color': {'type': valid_color_name,
                       'help': argparse.SUPPRESS},
             'program': {'type': str, 'help': argparse.SUPPRESS},
             'remind': {'type': str, 'help': argparse.SUPPRESS}}

OPTIONS = {
    'program': {
        "--client_id": {'default': gcalcli.__API_CLIENT_ID__},
        "--client_secret": {'default': gcalcli.__API_CLIENT_SECRET__},
        "--configFolder": {'default': None},
        "--defaultCalendar": {'default': [], 'action': 'append'}
    },
    'color': {
        '--color_owner': {'default': 'cyan'},
        '--color_writer': {'default': 'cyan'},
        '--color_reader': {'default': 'magenta'},
        '--color_freebusy': {'default': 'default'},
        '--color_date': {'default': 'yellow'},
        '--color_now-marker': {'default': 'brightred'},
        '--color_border': {'default': 'white'},
        '--color_title': {'default': 'brightyellow'},
    },
    'remind': {
        '--default_reminders': {'action': 'store_true',
                                'default': False}}
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


ALL_DEPRECATED_OPTS = {}
ALL_DEPRECATED_OPTS.update(OPTIONS['program'])
ALL_DEPRECATED_OPTS.update(OPTIONS['color'])
ALL_DEPRECATED_OPTS.update(OPTIONS['remind'])
