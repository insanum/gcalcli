import argparse
import functools
from typing import Any

from .printer import Printer, valid_color_name

printer = Printer()

CAMELS = {"--configFolder": "--config-folder",
          "--defaultCalendar": "--default-calendar"}


def warn_deprecated_opt(option_string):
    suggestion = 'Please use "{}", instead.\n'

    suggestion = (suggestion.format(CAMELS[option_string])
                  if option_string in CAMELS
                  else suggestion.format(option_string.replace('_', '-')))

    msg = ('WARNING: {} has been deprecated and will be removed in a future '
           'release.\n' + suggestion)
    printer.err_msg(msg.format(option_string))


class DeprecatedStore(argparse._StoreAction):
    def __call__(
            self, parser, namespace, values, option_string=None, **kwargs):
        warn_deprecated_opt(option_string)
        setattr(namespace, self.dest, values)


class DeprecatedStoreTrue(argparse._StoreConstAction):

    def __init__(self,
                 option_strings,
                 dest,
                 default=False,
                 required=False,
                 help=None):
        super(DeprecatedStoreTrue, self).__init__(
            option_strings=option_strings,
            dest=dest,
            const=True,
            default=default,
            required=required,
            help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        warn_deprecated_opt(option_string)
        setattr(namespace, self.dest, self.const)


class DeprecatedAppend(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        warn_deprecated_opt(option_string)
        items = argparse._copy.copy(
                argparse._ensure_value(namespace, self.dest, []))
        items.append(values)
        setattr(namespace, self.dest, items)


BASE_OPTS = {'program': {'type': str,
                         'help': argparse.SUPPRESS,
                         'action': DeprecatedStore},
             'color': {'type': valid_color_name,
                       'help': argparse.SUPPRESS,
                       'action': DeprecatedStore},
             'remind': {'help': argparse.SUPPRESS,
                        'action': DeprecatedStoreTrue}}


OPTIONS: dict[str, dict[str, Any]] = {
    'program': {
        "--client_id": {'default': None},
        "--client_secret": {'default': None},
        "--configFolder": {'default': None},
        "--defaultCalendar": {'default': [], 'action': DeprecatedAppend}
    },
    'color': {
        "--color_owner": {"default": "cyan"},
        "--color_writer": {"default": "cyan"},
        "--color_reader": {"default": "magenta"},
        "--color_freebusy": {"default": "default"},
        "--color_date": {"default": "yellow"},
        "--color_now_marker": {"default": "brightred"},
        "--color_border": {"default": "white"},
        "--color_title": {"default": "brightyellow"},
    },
    'remind': {
        '--default_reminders': {'action': DeprecatedStoreTrue,
                                'default': False}}
}


def parser_allow_deprecated(getter_func=None, name=None):
    if callable(getter_func):
        @functools.wraps(getter_func)
        def wrapped(*args, **kwargs):
            parser = getter_func()
            for arg, options in OPTIONS[name].items():
                parser.add_argument(
                        arg, default=options['default'], **BASE_OPTS[name])
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
