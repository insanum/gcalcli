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
# Authors: Eric Davis <http://www.insanum.com>                              #
#          Brian Hartvigsen <http://github.com/tresni>                      #
#          Joshua Crowgey <http://github.com/jcrowgey>                      #
# Home: https://github.com/insanum/gcalcli                                  #
#                                                                           #
# Everything you need to know (Google API Calendar v3): http://goo.gl/HfTGQ #
#                                                                           #
# ######################################################################### #
import json
import os
import signal
import sys
from collections import namedtuple

import truststore

from . import config, env, utils
from .argparsers import get_argument_parser, handle_unparsed
from .exceptions import GcalcliError
from .gcal import GoogleCalendarInterface
from .printer import Printer, valid_color_name
from .validators import (get_input, PARSABLE_DATE, PARSABLE_DURATION, REMINDER,
                         STR_ALLOW_EMPTY, STR_NOT_EMPTY)

CalName = namedtuple('CalName', ['name', 'color'])

EMPTY_CONFIG_TOML = """\
#:schema https://raw.githubusercontent.com/insanum/gcalcli/HEAD/data/config-schema.json

"""


def parse_cal_names(cal_names):
    cal_colors = {}
    for name in cal_names:
        cal_color = 'default'
        parts = name.split('#')
        parts_count = len(parts)
        if parts_count >= 1:
            cal_name = parts[0]

        if len(parts) == 2:
            cal_color = valid_color_name(parts[1])

        if len(parts) > 2:
            raise ValueError('Cannot parse calendar name: "%s"' % name)

        cal_colors[cal_name] = cal_color
    return [CalName(name=k, color=cal_colors[k]) for k in cal_colors.keys()]


def run_add_prompt(parsed_args, printer):
    if parsed_args.title is None:
        parsed_args.title = get_input(printer, 'Title: ', STR_NOT_EMPTY)
    if parsed_args.where is None:
        parsed_args.where = get_input(
            printer, 'Location: ', STR_ALLOW_EMPTY)
    if parsed_args.when is None:
        parsed_args.when = get_input(printer, 'When: ', PARSABLE_DATE)
    if parsed_args.duration is None and parsed_args.end is None:
        if parsed_args.allday:
            prompt = 'Duration (days): '
        else:
            prompt = 'Duration (human readable): '
        parsed_args.duration = get_input(printer, prompt, PARSABLE_DURATION)
    if parsed_args.description is None:
        parsed_args.description = get_input(
            printer, 'Description: ', STR_ALLOW_EMPTY)
    if not parsed_args.reminders:
        while True:
            r = get_input(
                    printer, 'Enter a valid reminder or ' '"." to end: ',
                    REMINDER)

            if r == '.':
                break
            n, m = utils.parse_reminder(str(r))
            parsed_args.reminders.append(str(n) + ' ' + m)


def main():
    # import trusted certificate store to enable SSL, e.g., behind firewalls
    truststore.inject_into_ssl()

    parser = get_argument_parser()
    try:
        argv = sys.argv[1:]
        gcalclirc = os.path.expanduser('~/.gcalclirc')
        if os.path.exists(gcalclirc):
            # We want .gcalclirc to be sourced before any other --flagfile
            # params since we may be told to use a specific config folder, we
            # need to store generated argv in temp variable
            tmp_argv = [f'@{gcalclirc}'] + argv
        else:
            tmp_argv = argv

        (parsed_args, unparsed) = parser.parse_known_args(tmp_argv)
    except Exception as e:
        sys.stderr.write(str(e))
        parser.print_usage()
        sys.exit(1)

    config_dir = env.default_config_dir()
    config_filepath = config_dir.joinpath('config.toml')
    if config_filepath.exists():
        with config_filepath.open('rb') as config_file:
            opts_from_config = config.Config.from_toml(config_file)
    else:
        opts_from_config = config.Config()

    if parsed_args.config_folder:
        parsed_args.config_folder = parsed_args.config_folder.expanduser()
        gcalclirc_path = parsed_args.config_folder.joinpath('gcalclirc')
        if gcalclirc_path.exists():
            # TODO: Should this precedence be flipped to:
            # ['@~/.gcalclirc', '@CONFIG_FOLDER/gcalclirc', ...]?
            tmp_argv = [f'@{gcalclirc_path}'] + (
                tmp_argv if parsed_args.includeRc else argv
            )

        namespace_from_config = opts_from_config.to_argparse_namespace()
        # Pull week_start aside and set it manually after parse_known_args.
        # TODO: Figure out why week_start from opts_from_config getting through.
        week_start = namespace_from_config.week_start
        namespace_from_config.week_start = None
        (parsed_args, unparsed) = parser.parse_known_args(
            tmp_argv, namespace=namespace_from_config)
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

    if len(parsed_args.calendar) == 0:
        parsed_args.calendar = parsed_args.default_calendars

    cal_names = parse_cal_names(parsed_args.calendar)
    # Only ignore calendars if they're not explicitly in --calendar list.
    parsed_args.ignore_calendars[:] = [
        c
        for c in parsed_args.ignore_calendars
        if c not in [c2.name for c2 in cal_names]
    ]
    userless_mode = bool(os.environ.get('GCALCLI_USERLESS_MODE'))
    gcal = GoogleCalendarInterface(
        cal_names=cal_names,
        printer=printer,
        userless_mode=userless_mode,
        **vars(parsed_args),
    )

    try:
        if parsed_args.command == 'list':
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
                    'text editor...'
                )
                if not config_filepath.exists():
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

    except GcalcliError as exc:
        printer.err_msg(str(exc))
        sys.exit(1)


def SIGINT_handler(signum, frame):
    sys.stderr.write('Signal caught, bye!\n')
    sys.exit(1)


signal.signal(signal.SIGINT, SIGINT_handler)


if __name__ == '__main__':
    main()
