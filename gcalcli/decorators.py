from __future__ import absolute_import
import argparse

from gcalcli.printer import valid_color_name

_deprecated_opts = (
    ("--color_", "--color-")
)


def parser_allow_deprecated(getter_func):
    def wrapped(*args, **kwargs):
        color_parser = getter_func()
        color_parser.add_argument(
                "--color_owner", dest="color_owner",  default="cyan",
                type=valid_color_name,
                help=argparse.SUPPRESS)
        color_parser.add_argument(
                "--color_writer", default="green", type=valid_color_name,
                help=argparse.SUPPRESS)
        color_parser.add_argument(
                "--color_reader", default="magenta", type=valid_color_name,
                help=argparse.SUPPRESS)
        color_parser.add_argument(
                "--color_freebusy", default="default", type=valid_color_name,
                help=argparse.SUPPRESS)
        color_parser.add_argument(
                "--color_date", default="yellow", type=valid_color_name,
                help=argparse.SUPPRESS)
        color_parser.add_argument(
                "--color_now-marker",
                default="brightred",
                type=valid_color_name,
                help=argparse.SUPPRESS)
        color_parser.add_argument(
                "--color_border", default="white", type=valid_color_name,
                help=argparse.SUPPRESS)
        color_parser.add_argument(
                "--color_title", default="brightyellow", type=valid_color_name,
                help=argparse.SUPPRESS)
        return color_parser
    return wrapped
