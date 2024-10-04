#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
#
# ######################################################################### #
#                                                                           #
#                                      (           (     (                  #
#               (         (     (      )\ )   (    )\ )  )\ )               #
#               )\ )      )\    )\    (()/(   )\  (()/( (()/(               #
#              (()/(    (((_)((((_)(   /(_))(((_)  /(_)) /(_))              #
#               /(_))_  )\___ )\ _ )\ (_))  )\___ (_))  (_))                #
#              (_)) __|((/ __|(_)_\(_)| |  ((/ __|| |   |_ _|               #
#                | (_ | | (__  / _ \  | |__ | (__ | |__  | |                #
#                 \___|  \___|/_/ \_\ |____| \___||____||___|               #
#                                                                           #
# Authors: Eric Davis <https://www.insanum.com>                             #
#          Brian Hartvigsen <https://github.com/tresni>                     #
#          Joshua Crowgey <https://github.com/jcrowgey>                     #
# Maintainers: David Barnett <https://github.com/dbarnett>                  #
# Home: https://github.com/insanum/gcalcli                                  #
#                                                                           #
# Everything you need to know (Google API Calendar v3): http://goo.gl/HfTGQ #
#                                                                           #
# ######################################################################### #


# Import trusted certificate store to enable SSL, e.g., behind firewalls.
# Must be called as early as possible to avoid bugs.
# fmt: off
import truststore; truststore.inject_into_ssl()  # noqa: I001,E702
# fmt: on
# ruff: noqa: E402


import json
import os
import pathlib
import re
import signal
import sys
from argparse import ArgumentTypeError
from collections import namedtuple

from . import config, env, utils
from .argparsers import get_argument_parser, handle_unparsed
from .exceptions import GcalcliError
from .gcal import GoogleCalendarInterface
from .printer import Printer, valid_color_name
from .validators import (
    DATE_INPUT_DESCRIPTION,
    PARSABLE_DATE,
    PARSABLE_DURATION,
    REMINDER,
    STR_ALLOW_EMPTY,
    STR_NOT_EMPTY,
    get_input,
)

CalName = namedtuple('CalName', ['name', 'color'])

EMPTY_CONFIG_TOML = """\
#:schema https://raw.githubusercontent.com/insanum/gcalcli/HEAD/data/config-schema.json

"""


def rsplit_unescaped_hash(string):
    # Use regex to find parts before/after last unescaped hash separator.
    # Sadly, all the "proper solutions" are even more questionable:
    # https://stackoverflow.com/questions/4020539/process-escape-sequences
    match = re.match(
        r"""(?x)
            ^((?:\\.|[^\\])*)
            [#]
            ((?:\\.|[^#\\])*)$
        """,
        string
    )
    if not match:
        return (string, None)
    # Unescape and return (part1, part2)
    return tuple(re.sub(r'\\(.)', r'\1', p)
                 for p in match.group(1, 2))


def parse_cal_names(cal_names: list[str], printer: Printer):
    cal_colors = {}
    for name in cal_names:
        cal_color = 'default'
        p1, p2 = rsplit_unescaped_hash(name)
        if p2 is not None:
            try:
                name, cal_color = p1, valid_color_name(p2)
            except ArgumentTypeError:
                printer.debug_msg(
                    f'Using entire name {name!r} as cal name.\n'
                    f'Change {p1!r} to a valid color name if intended to be a '
                    'color (or otherwise consider escaping "#" chars to "\\#").'
                    '\n'
                )

        cal_colors[name] = cal_color
    return [CalName(name=k, color=v) for k, v in cal_colors.items()]


def run_add_prompt(parsed_args, printer):
    if not any(
        a is None
        for a in (
            parsed_args.title,
            parsed_args.where,
            parsed_args.when,
            parsed_args.duration or parsed_args.end,
            parsed_args.description,
            parsed_args.reminders or parsed_args.default_reminders,
        )
    ):
        return
    printer.msg(
        'Prompting for unfilled values.\n'
        'Run with --noprompt to leave them unfilled without prompting.\n'
    )
    if parsed_args.title is None:
        parsed_args.title = get_input(printer, 'Title: ', STR_NOT_EMPTY)
    if parsed_args.where is None:
        parsed_args.where = get_input(printer, 'Location: ', STR_ALLOW_EMPTY)
    if parsed_args.when is None:
        parsed_args.when = get_input(
            printer,
            'When (? for help): ',
            PARSABLE_DATE,
            help=f'Expected format: {DATE_INPUT_DESCRIPTION}',
        )
    if parsed_args.duration is None and parsed_args.end is None:
        if parsed_args.allday:
            prompt = 'Duration (days): '
        else:
            prompt = 'Duration (human readable): '
        parsed_args.duration = get_input(printer, prompt, PARSABLE_DURATION)
    if parsed_args.description is None:
        parsed_args.description = get_input(
            printer, 'Description: ', STR_ALLOW_EMPTY
        )
    if not parsed_args.reminders and not parsed_args.default_reminders:
        while True:
            r = get_input(
                printer, 'Enter a valid reminder or ' '"." to end: ', REMINDER
            )

            if r == '.':
                break
            n, m = utils.parse_reminder(str(r))
            parsed_args.reminders.append(str(n) + ' ' + m)


def main():
    parser = get_argument_parser()
    argv = sys.argv[1:]

    rc_paths = [
        pathlib.Path('~/.gcalclirc').expanduser(),
        env.config_dir().joinpath('gcalclirc'),
    ]
    # Note: Order is significant here, so precedence is
    # ~/.gcalclirc < CONFIGDIR/gcalclirc < explicit args
    fromfile_args = [f'@{rc}' for rc in rc_paths if rc.exists()]

    try:
        (parsed_args, unparsed) = parser.parse_known_args(fromfile_args + argv)
    except Exception as e:
        sys.stderr.write(str(e))
        parser.print_usage()
        sys.exit(1)

    if parsed_args.config_folder:
        parsed_args.config_folder = parsed_args.config_folder.expanduser()
    # Re-evaluate rc_paths in case --config-folder or something was updated.
    # Note this could resolve strangely if you e.g. have a gcalclirc file that
    # contains --noincluderc or overrides --config-folder from inside config
    # folder. If that causes problems... don't do that.
    rc_paths = [
        pathlib.Path('~/.gcalclirc').expanduser(),
        parsed_args.config_folder.joinpath('gcalclirc')
        if parsed_args.config_folder
        else None,
    ]
    fromfile_args = [f'@{rc}' for rc in rc_paths if rc and rc.exists()]

    config_filepath = env.config_file()
    if config_filepath.exists():
        with config_filepath.open('rb') as config_file:
            opts_from_config = config.Config.from_toml(config_file)
    else:
        opts_from_config = config.Config()

    namespace_from_config = opts_from_config.to_argparse_namespace()
    # Pull week_start aside and set it manually after parse_known_args.
    # TODO: Figure out why week_start from opts_from_config getting through.
    week_start = namespace_from_config.week_start
    namespace_from_config.week_start = None
    if parsed_args.includeRc:
        argv = fromfile_args + argv
    (parsed_args, unparsed) = parser.parse_known_args(
        argv, namespace=namespace_from_config
    )
    if parsed_args.week_start is None:
        parsed_args.week_start = week_start
    if parsed_args.config_folder:
        parsed_args.config_folder = parsed_args.config_folder.expanduser()

    printer = Printer(
            conky=parsed_args.conky, use_color=parsed_args.color,
            art_style=parsed_args.lineart
    )

    if unparsed:
        try:
            parsed_args = handle_unparsed(unparsed, parsed_args)
        except Exception as e:
            sys.stderr.write(str(e))
            parser.print_usage()
            sys.exit(1)

    if parsed_args.locale:
        try:
            utils.set_locale(parsed_args.locale)
        except ValueError as exc:
            printer.err_msg(str(exc))

    cal_names = set_resolved_calendars(parsed_args, printer=printer)

    userless_mode = bool(os.environ.get('GCALCLI_USERLESS_MODE'))
    if parsed_args.command in ('config', 'util'):
        gcal = None
    else:
        gcal = GoogleCalendarInterface(
            cal_names=cal_names,
            printer=printer,
            userless_mode=userless_mode,
            # TODO: Avoid heavy unnecessary setup in general, remove override.
            do_eager_init=parsed_args.command != 'init',
            **vars(parsed_args),
        )

    try:
        if parsed_args.command == 'init':
            gcal.SetupAuth()

        elif parsed_args.command == 'list':
            gcal.ListAllCalendars()

        elif parsed_args.command == 'agenda':
            gcal.AgendaQuery(start=parsed_args.start, end=parsed_args.end)

        elif parsed_args.command == 'agendaupdate':
            gcal.AgendaUpdate(parsed_args.file)

        elif parsed_args.command == 'updates':
            gcal.UpdatesQuery(
                    last_updated_datetime=parsed_args.since,
                    start=parsed_args.start,
                    end=parsed_args.end)

        elif parsed_args.command == 'conflicts':
            gcal.ConflictsQuery(
                    search_text=parsed_args.text,
                    start=parsed_args.start,
                    end=parsed_args.end)

        elif parsed_args.command == 'calw':
            gcal.CalQuery(
                    parsed_args.command, count=parsed_args.weeks,
                    start_text=parsed_args.start
            )

        elif parsed_args.command == 'calm':
            gcal.CalQuery(parsed_args.command, start_text=parsed_args.start)

        elif parsed_args.command == 'quick':
            if not parsed_args.text:
                printer.err_msg('Error: invalid event text\n')
                sys.exit(1)

            # allow unicode strings for input
            gcal.QuickAddEvent(
                    parsed_args.text, reminders=parsed_args.reminders
            )

        elif parsed_args.command == 'add':
            if parsed_args.prompt:
                run_add_prompt(parsed_args, printer)

            # calculate "when" time:
            try:
                estart, eend = utils.get_times_from_duration(
                    parsed_args.when,
                    duration=parsed_args.duration,
                    end=parsed_args.end,
                    allday=parsed_args.allday)
            except ValueError as exc:
                printer.err_msg(str(exc))
                # Since we actually need a valid start and end time in order to
                # add the event, we cannot proceed.
                raise

            gcal.AddEvent(parsed_args.title, parsed_args.where, estart, eend,
                          parsed_args.description, parsed_args.who,
                          parsed_args.reminders, parsed_args.event_color)

        elif parsed_args.command == 'search':
            gcal.TextQuery(
                    parsed_args.text[0], start=parsed_args.start,
                    end=parsed_args.end
            )

        elif parsed_args.command == 'delete':
            gcal.ModifyEvents(
                    gcal._delete_event, parsed_args.text[0],
                    start=parsed_args.start, end=parsed_args.end,
                    expert=parsed_args.iamaexpert
            )

        elif parsed_args.command == 'edit':
            gcal.ModifyEvents(
                    gcal._edit_event, parsed_args.text[0],
                    start=parsed_args.start, end=parsed_args.end
            )

        elif parsed_args.command == 'remind':
            gcal.Remind(
                    parsed_args.minutes, parsed_args.cmd,
                    use_reminders=parsed_args.use_reminders
            )

        elif parsed_args.command == 'import':
            gcal.ImportICS(
                    parsed_args.verbose, parsed_args.dump,
                    parsed_args.reminders, parsed_args.file
            )

        elif parsed_args.command == 'config':
            if parsed_args.subcommand == 'edit':
                printer.msg(
                    f'Launching {utils.shorten_path(config_filepath)} in a '
                    'text editor...\n'
                )
                if not config_filepath.exists():
                    config_filepath.parent.mkdir(parents=True, exist_ok=True)
                    with open(config_filepath, 'w') as f:
                        f.write(EMPTY_CONFIG_TOML)
                utils.launch_editor(config_filepath)

        elif parsed_args.command == 'util':
            if parsed_args.subcommand == 'config-schema':
                printer.debug_msg(
                    'Outputting schema for config.toml files. This can be '
                    'saved to a file and used in a directive like '
                    '#:schema my-schema.json\n'
                )
                schema = config.Config.json_schema()
                print(json.dumps(schema, indent=2))
            elif parsed_args.subcommand == 'reset-cache':
                deleted_something = False
                for cache_filepath in env.data_file_paths('cache'):
                    if cache_filepath.exists():
                        printer.msg(
                            f'Deleting cache file from {cache_filepath}...\n'
                        )
                        cache_filepath.unlink(missing_ok=True)
                        deleted_something = True
                if not deleted_something:
                    printer.msg(
                        'No cache file found. Exiting without deleting '
                        'anything...\n'
                    )
            elif parsed_args.subcommand == 'inspect-auth':
                auth_data = utils.inspect_auth()
                for k, v in auth_data.items():
                    printer.msg(f"{k}: {v}\n")
                if auth_data.get('format', 'unknown') != 'unknown':
                    printer.msg(
                        "\n"
                        "The grant's entry under "
                        "https://myaccount.google.com/connections should also "
                        "list creation time and other info Google provides on "
                        "the access grant.\n"
                        'Hint: filter by "Access to: Calendar" if you have '
                        "trouble finding the right one.\n")
                else:
                    printer.err_msg("No existing auth token found\n")

    except GcalcliError as exc:
        printer.err_msg(str(exc))
        sys.exit(1)


def set_resolved_calendars(parsed_args, printer: Printer) -> list[str]:
    multiple_allowed = not hasattr(parsed_args, 'calendar')

    # Reflect .calendar into .calendars (as list).
    if hasattr(parsed_args, 'calendar') and not hasattr(
        parsed_args, 'calendars'
    ):
        parsed_args.calendars = (
            [parsed_args.calendar] if parsed_args.calendar else []
        )
    # If command didn't request calendar or calendars, bail out with empty list.
    # Note: this means if you forget parents=[calendar_parser] on a subparser,
    # you'll hit this case and any global/default cals will be ignored.
    if not hasattr(parsed_args, 'calendars'):
        return []

    if not parsed_args.calendars:
        for cals_type, cals in [
            ('global calendars', parsed_args.global_calendars),
            ('default-calendars', parsed_args.default_calendars),
        ]:
            if len(cals) > 1 and not multiple_allowed:
                printer.debug_msg(
                    f"Can't use multiple {cals_type} for command "
                    f"`{parsed_args.command}`. Must select --calendar "
                    "explicitly.\n"
                )
                continue
            if cals:
                parsed_args.calendars = cals
                break
    elif len(parsed_args.calendars) > 1 and not multiple_allowed:
        printer.err_msg(
            'Multiple target calendars specified! Please only pass a '
            'single --calendar if you want it to be used.\n'
        )
        printer.msg(
            'Note: consider using --noincluderc if additional '
            'calendars may be coming from gcalclirc.\n'
        )

    cal_names = parse_cal_names(parsed_args.calendars, printer=printer)
    # Only ignore calendars if they're not explicitly in --calendar list.
    parsed_args.ignore_calendars[:] = [
        c
        for c in parsed_args.ignore_calendars
        if c not in [c2.name for c2 in cal_names]
    ]

    return cal_names


def SIGINT_handler(signum, frame):
    sys.stderr.write('Signal caught, bye!\n')
    sys.exit(1)


signal.signal(signal.SIGINT, SIGINT_handler)


if __name__ == '__main__':
    main()
