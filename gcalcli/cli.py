#!/usr/bin/env python
#
#############################################################################
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
#############################################################################
import os
import signal
import sys
from collections import namedtuple

from gcalcli import utils
from gcalcli.argparsers import get_argument_parser, handle_unparsed
from gcalcli.exceptions import GcalcliError
from gcalcli.gcal import GoogleCalendarInterface
from gcalcli.printer import Printer, valid_color_name
from gcalcli.validators import (
        PARSABLE_DATE, REMINDER, STR_ALLOW_EMPTY, STR_NOT_EMPTY,
        PARSABLE_DURATION, get_input
)

CalName = namedtuple('CalName', ['name', 'color'])


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
    if parsed_args.duration is None:
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
    parser = get_argument_parser()
    try:
        argv = sys.argv[1:]
        gcalclirc = os.path.expanduser('~/.gcalclirc')
        if os.path.exists(gcalclirc):
            # We want .gcalclirc to be sourced before any other --flagfile
            # params since we may be told to use a specific config folder, we
            # need to store generated argv in temp variable
            tmp_argv = ['@%s' % gcalclirc, ] + argv
        else:
            tmp_argv = argv

        (parsed_args, unparsed) = parser.parse_known_args(tmp_argv)
    except Exception as e:
        sys.stderr.write(str(e))
        parser.print_usage()
        sys.exit(1)

    if parsed_args.config_folder:
        if not os.path.exists(os.path.expanduser(parsed_args.config_folder)):
            os.makedirs(os.path.expanduser(parsed_args.config_folder))
        if os.path.exists(os.path.expanduser('%s/gcalclirc' %
                                             parsed_args.config_folder)):
            rc_path = ['@%s/gcalclirc' % parsed_args.config_folder, ]
            if not parsed_args.includeRc:
                tmp_argv = rc_path + argv
            else:
                tmp_argv = rc_path + tmp_argv

        (parsed_args, unparsed) = parser.parse_known_args(tmp_argv)

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
        parsed_args.calendar = parsed_args.defaultCalendar

    cal_names = parse_cal_names(parsed_args.calendar)
    gcal = GoogleCalendarInterface(
            cal_names=cal_names, printer=printer, **vars(parsed_args)
    )

    try:
        if parsed_args.command == 'list':
            gcal.ListAllCalendars()

        elif parsed_args.command == 'agenda':
            gcal.AgendaQuery(start=parsed_args.start, end=parsed_args.end)

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
                        parsed_args.when, parsed_args.duration,
                        parsed_args.allday
                )
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

    except GcalcliError as exc:
        printer.err_msg(str(exc))
        sys.exit(1)


def SIGINT_handler(signum, frame):
    sys.stderr.write('Signal caught, bye!\n')
    sys.exit(1)


signal.signal(signal.SIGINT, SIGINT_handler)


if __name__ == '__main__':
    main()
