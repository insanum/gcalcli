import os
import re
import shlex
import httplib2
import time
import textwrap
import json
import random
import sys
from unicodedata import east_asian_width
try:
    import cPickle as pickle
except Exception:
    import pickle

from gcalcli import __program__, __version__
from gcalcli import utils
from gcalcli.utils import days_since_epoch
from gcalcli.validators import (
    get_input, get_override_color_id, STR_NOT_EMPTY, PARSABLE_DATE, STR_TO_INT,
    VALID_COLORS, STR_ALLOW_EMPTY, REMINDER, PARSABLE_DURATION
)
from gcalcli.exceptions import GcalcliError
from gcalcli.printer import Printer
from gcalcli.conflicts import ShowConflicts

from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
from dateutil.tz import tzlocal
from dateutil.parser import parse
from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client import tools
from collections import namedtuple

EventTitle = namedtuple('EventTitle', ['title', 'color'])


class GoogleCalendarInterface:

    cache = {}
    all_cals = []
    now = datetime.now(tzlocal())
    agenda_length = 5
    conflicts_lookahead_days = 30
    max_retries = 5
    auth_http = None
    cal_service = None

    ACCESS_OWNER = 'owner'
    ACCESS_WRITER = 'writer'
    ACCESS_READER = 'reader'
    ACCESS_FREEBUSY = 'freeBusyReader'

    UNIWIDTH = {'W': 2, 'F': 2, 'N': 1, 'Na': 1, 'H': 1, 'A': 1}

    def __init__(self, cal_names=[], printer=Printer(), **options):
        self.cals = []
        self.printer = printer
        self.options = options

        self.details = options.get('details', {})
        # stored as detail, but provided as option: TODO: fix that
        self.details['width'] = options.get('width', 80)
        self._get_cached()

        self._select_cals(cal_names)

    def _select_cals(self, selected_names):
        if self.cals:
            raise GcalcliError('this object should not already have cals')

        if not selected_names:
            self.cals = self.all_cals
            return

        for cal_name in selected_names:
            matches = []
            for self_cal in self.all_cals:
                # For exact match, we should match only 1 entry and accept
                # the first entry.  Should honor access role order since
                # it happens after _get_cached()
                if cal_name.name == self_cal['summary']:
                    # This makes sure that if we have any regex matches
                    # that we toss them out in favor of the specific match
                    matches = [self_cal]
                    self_cal['colorSpec'] = cal_name.color
                    break
                # Otherwise, if the calendar matches as a regex, append
                # it to the list of potential matches
                elif re.search(cal_name.name, self_cal['summary'], flags=re.I):
                    matches.append(self_cal)
                    self_cal['colorSpec'] = cal_name.color
            # Add relevant matches to the list of calendars we want to
            # operate against
            self.cals += matches

    @staticmethod
    def _localize_datetime(dt):
        if not hasattr(dt, 'tzinfo'):  # Why are we skipping these?
            return dt
        if dt.tzinfo is None:
            return dt.replace(tzinfo=tzlocal())
        else:
            return dt.astimezone(tzlocal())

    def _retry_with_backoff(self, method):
        for n in range(self.max_retries):
            try:
                return method.execute()
            except HttpError as e:
                error = json.loads(e.content)
                error = error.get('error')
                if error.get('code') == '403' and \
                        error.get('errors')[0].get('reason') \
                        in ['rateLimitExceeded', 'userRateLimitExceeded']:
                    time.sleep((2 ** n) + random.random())
                else:
                    raise

        return None

    def _google_auth(self):
        from argparse import Namespace
        if not self.auth_http:
            if self.options['config_folder']:
                storage = Storage(
                        os.path.expanduser(
                                '%s/oauth' % self.options['config_folder']
                        )
                )
            else:
                storage = Storage(os.path.expanduser('~/.gcalcli_oauth'))
            credentials = storage.get()

            if credentials is None or credentials.invalid:
                credentials = tools.run_flow(
                    OAuth2WebServerFlow(
                        client_id=self.options['client_id'],
                        client_secret=self.options['client_secret'],
                        scope=['https://www.googleapis.com/auth/calendar'],
                        user_agent=__program__ + '/' + __version__
                    ),
                    storage,
                    Namespace(**self.options)
                )

            self.auth_http = credentials.authorize(httplib2.Http())

        return self.auth_http

    def get_cal_service(self):
        if not self.cal_service:
            self.cal_service = build(serviceName='calendar',
                                     version='v3',
                                     http=self._google_auth())

        return self.cal_service

    def _get_cached(self):
        if self.options['config_folder']:
            cache_file = os.path.expanduser(
                    '%s/cache' % self.options['config_folder']
            )
        else:
            cache_file = os.path.expanduser('~/.gcalcli_cache')

        if self.options['refresh_cache']:
            try:
                os.remove(cache_file)
            except OSError:
                pass
                # fall through

        self.cache = {}
        self.all_cals = []

        if self.options['use_cache']:
            # note that we need to use pickle for cache data since we stuff
            # various non-JSON data in the runtime storage structures
            try:
                with open(cache_file, 'rb') as _cache_:
                    self.cache = pickle.load(_cache_)
                    self.all_cals = self.cache['all_cals']
                # XXX assuming data is valid, need some verification check here
                return
            except IOError:
                pass
                # fall through

        cal_list = self._retry_with_backoff(
            self.get_cal_service().calendarList().list()
        )

        while True:
            for cal in cal_list['items']:
                self.all_cals.append(cal)
            page_token = cal_list.get('nextPageToken')
            if page_token:
                cal_list = self._retry_with_backoff(
                    self.get_cal_service().calendarList().list(
                        pageToken=page_token
                    )
                )
            else:
                break

        self.all_cals.sort(key=lambda x: x['accessRole'])

        if self.options['use_cache']:
            self.cache['all_cals'] = self.all_cals
            with open(cache_file, 'wb') as _cache_:
                pickle.dump(self.cache, _cache_)

    def _calendar_color(self, event, override_color=False):
        ansi_codes = {
            '1': 'brightblue',
            '2': 'brightgreen',
            '3': 'brightmagenta',
            '4': 'magenta',
            '5': 'brightyellow',
            '6': 'brightred',
            '7': 'brightcyan',
            '8': 'brightblack',
            '9': 'blue',
            '10': 'green',
            '11': 'red'
        }
        if event.get('gcalcli_cal') is None:
            return 'default'
        else:
            cal = event['gcalcli_cal']
        if override_color:
            return ansi_codes[event['colorId']]
        elif cal.get('colorSpec', None):
            return cal['colorSpec']
        elif cal['accessRole'] == self.ACCESS_OWNER:
            return self.options['color_owner']
        elif cal['accessRole'] == self.ACCESS_WRITER:
            return self.options['color_writer']
        elif cal['accessRole'] == self.ACCESS_READER:
            return self.options['color_reader']
        elif cal['accessRole'] == self.ACCESS_FREEBUSY:
            return self.options['color_freebusy']
        else:
            return 'default'

    def _valid_title(self, event):
        if 'summary' in event and event['summary'].strip():
            return event['summary']
        else:
            return '(No title)'

    def _isallday(self, event):
        return event['s'].hour == 0 and event['s'].minute == 0 and \
            event['e'].hour == 0 and event['e'].minute == 0

    def _cal_monday(self, day_num):
        """Shift the day number if we're doing cal monday, or cal_weekend is
        false, since that also means we're starting on day 1
        """
        if self.options['cal_monday'] or not self.options['cal_weekend']:
            day_num -= 1
            if day_num < 0:
                day_num = 6
        return day_num

    def _event_time_in_range(self, e_time, r_start, r_end):
        return e_time >= r_start and e_time < r_end

    def _event_spans_time(self, e_start, e_end, time_point):
        return e_start < time_point and e_end >= time_point

    def _format_title(self, event, allday=False):
        titlestr = self._valid_title(event)
        if allday:
            return titlestr
        elif self.options['military']:
            return ' '.join([event['s'].strftime('%H:%M'), titlestr])
        else:
            return ' '.join([event['s'].strftime('%I:%M').lstrip('0') +
                            event['s'].strftime('%p').lower(), titlestr])

    def _add_reminders(self, event, reminders=None):
        if reminders or not self.options['default_reminders']:
            event['reminders'] = {'useDefault': False,
                                  'overrides': []}
            for r in reminders:
                n, m = utils.parse_reminder(r)
                event['reminders']['overrides'].append({'minutes': n,
                                                        'method': m})
        return event

    def _get_week_events(self, start_dt, end_dt, event_list):
        week_events = [[] for _ in range(7)]

        now_in_week = True
        now_marker_printed = False
        if self.now < start_dt or self.now > end_dt:
            now_in_week = False

        for event in event_list:
            event_daynum = self._cal_monday(int(event['s'].strftime('%w')))
            event_allday = self._isallday(event)

            event_end_date = event['e']
            if event_allday:
                # NOTE(slwaqo): in allDay events end date is always set as
                # day+1 and hour 0:00 so to not display it one day more, it's
                # necessary to lower it by one day
                event_end_date = event['e'] - timedelta(days=1)

            event_is_today = self._event_time_in_range(
                    event['s'], start_dt, end_dt
            )

            event_continues_today = self._event_spans_time(
                    event['s'], event_end_date, start_dt
            )

            # NOTE(slawqo): it's necessary to process events which starts in
            # current period of time but for all day events also to process
            # events which was started before current period of time and are
            # still continue in current period of time
            if event_is_today or (event_allday and event_continues_today):
                color_as_now_marker = False

                if now_in_week and not now_marker_printed:
                    if (days_since_epoch(self.now) <
                            days_since_epoch(event['s'])):
                        week_events[event_daynum].append(
                                EventTitle(
                                    '\n' + self.options['cal_width'] * '-',
                                    self.options['color_now_marker']
                                )
                        )
                        now_marker_printed = True

                    # We don't want to recolor all day events, but ignoring
                    # them leads to issues where the 'now' marker misprints
                    # into the wrong day.  This resolves the issue by skipping
                    # all day events for specific coloring but not for previous
                    # or next events
                    elif self.now >= event['s'] and \
                            self.now <= event_end_date and \
                            not event_allday:
                        # line marker is during the event (recolor event)
                        color_as_now_marker = True
                        now_marker_printed = True

                if color_as_now_marker:
                    event_color = self.options['color_now_marker']
                else:
                    if self.options['override_color'] and event.get('colorId'):
                        event_color = self._calendar_color(
                                event, override_color=True
                        )
                    else:
                        event_color = self._calendar_color(event)

                # NOTE(slawqo): for all day events it's necessary to add event
                # to more than one day in week_events
                titlestr = self._format_title(event, allday=event_allday)
                if event_allday and event['s'] < event_end_date:
                    if event_end_date > end_dt:
                        end_daynum = 6
                    else:
                        end_daynum = \
                            self._cal_monday(
                                    int(event_end_date.strftime('%w'))
                            )
                    if event_daynum > end_daynum:
                        event_daynum = 0
                    for day in range(event_daynum, end_daynum + 1):
                        week_events[day].append(
                                EventTitle('\n' + titlestr, event_color)
                        )
                else:
                    # newline and empty string are the keys to turn off
                    # coloring
                    week_events[event_daynum].append(
                            EventTitle('\n' + titlestr, event_color)
                    )
        return week_events

    def _printed_len(self, string):
        # We need to treat everything as unicode for this to actually give
        # us the info we want.  Date string were coming in as `str` type
        # so we convert them to unicode and then check their size. Fixes
        # the output issues we were seeing around non-US locale strings
        return sum(
                self.UNIWIDTH[east_asian_width(char)] for char in string
        )

    def _word_cut(self, word):
        stop = 0
        for i, char in enumerate(word):
            stop += self._printed_len(char)
            if stop >= self.options['cal_width']:
                return stop, i + 1

    def _next_cut(self, string):
        print_len = 0

        words = string.split()
        word_lens = []
        for i, word in enumerate(words):
            word_lens.append(self._printed_len(word))

            if (word_lens[-1] + print_len) >= self.options['cal_width']:
                # this many words is too many, try to cut at the prev word
                cut_idx = len(' '.join(words[:i]))

                # first word is too long, we must cut inside it
                if cut_idx == 0:
                    return self._word_cut(word)

                return (print_len, cut_idx)
            print_len = sum(word_lens) + i  # +i for the space between words

        return (print_len, len(' '.join(words[:i])))

    def _get_cut_index(self, event_string):
        print_len = self._printed_len(event_string)

        # newline in string is a special case
        idx = event_string.find('\n')
        if idx > -1 and idx <= self.options['cal_width']:
            return (self._printed_len(event_string[:idx]),
                    len(event_string[:idx]))

        if print_len <= self.options['cal_width']:
            return (print_len, len(event_string))

        else:
            # we must cut: _next_cut will loop until we find the right spot
            return self._next_cut(event_string)

    def _GraphEvents(self, cmd, start_datetime, count, event_list):
        # ignore started events (i.e. events that start previous day and end
        # start day)

        color_border = self.options['color_border']

        while (len(event_list) and event_list[0]['s'] < start_datetime):
            event_list = event_list[1:]

        day_width_line = self.options['cal_width'] * self.printer.art['hrz']
        days = 7 if self.options['cal_weekend'] else 5
        # Get the localized day names... January 1, 2001 was a Monday
        day_names = [date(2001, 1, i + 1).strftime('%A') for i in range(days)]
        if not self.options['cal_monday'] or not self.options['cal_weekend']:
            day_names = day_names[6:] + day_names[:6]

        def build_divider(left, center, right):
            return (
                self.printer.art[left] + day_width_line +
                ((days - 1) * (self.printer.art[center] + day_width_line)) +
                self.printer.art[right]
            )

        week_top = build_divider('ulc', 'ute', 'urc')
        week_divider = build_divider('lte', 'crs', 'rte')
        week_bottom = build_divider('llc', 'bte', 'lrc')
        empty_day = self.options['cal_width'] * ' '

        if cmd == 'calm':
            # month titlebar
            month_title_top = build_divider('ulc', 'hrz', 'urc')
            self.printer.msg(month_title_top + '\n', color_border)

            month_title = start_datetime.strftime('%B %Y')
            month_width = (self.options['cal_width'] * days) + (days - 1)
            month_title += ' ' * (month_width - self._printed_len(month_title))

            self.printer.art_msg('vrt', color_border)
            self.printer.msg(month_title, self.options['color_date'])
            self.printer.art_msg('vrt', color_border)

            month_title_bottom = build_divider('lte', 'ute', 'rte')
            self.printer.msg('\n' + month_title_bottom + '\n', color_border)
        else:
            # week titlebar
            # month title bottom takes care of this when cmd='calm'
            self.printer.msg(week_top + '\n', color_border)

        # weekday labels
        self.printer.art_msg('vrt', color_border)
        for day_name in day_names:
            day_name += ' ' * (
                    self.options['cal_width'] - self._printed_len(day_name)
            )
            self.printer.msg(day_name, self.options['color_date'])
            self.printer.art_msg('vrt', color_border)

        self.printer.msg('\n' + week_divider + '\n', color_border)
        cur_month = start_datetime.strftime('%b')

        # get date range objects for the first week
        if cmd == 'calm':
            day_num = self._cal_monday(int(start_datetime.strftime('%w')))
            start_datetime = (start_datetime - timedelta(days=day_num))
        start_week_datetime = start_datetime
        end_week_datetime = (start_week_datetime + timedelta(days=7))

        for i in range(count):
            # create and print the date line for a week
            for j in range(days):
                if cmd == 'calw':
                    d = (start_week_datetime +
                         timedelta(days=j)).strftime('%d %b')
                else:  # (cmd == 'calm'):
                    d = (start_week_datetime +
                         timedelta(days=j)).strftime('%d')
                    if cur_month != (start_week_datetime +
                                     timedelta(days=j)).strftime('%b'):
                        d = ''
                tmp_date_color = self.options['color_date']

                fmt_now = (start_week_datetime +
                           timedelta(days=j)).strftime('%d%b%Y')
                if self.now.strftime('%d%b%Y') == fmt_now:
                    tmp_date_color = self.options['color_now_marker']
                    d += ' **'

                d += ' ' * (self.options['cal_width'] - self._printed_len(d))

                # print dates
                self.printer.art_msg('vrt', color_border)
                self.printer.msg(d, tmp_date_color)

            self.printer.art_msg('vrt', color_border)
            self.printer.msg('\n')

            week_events = self._get_week_events(
                    start_week_datetime, end_week_datetime, event_list
            )

            # get date range objects for the next week
            start_week_datetime = end_week_datetime
            end_week_datetime = (end_week_datetime + timedelta(days=7))

            while True:
                # keep looping over events by day, printing one line at a time
                # stop when everything has been printed
                done = True
                self.printer.art_msg('vrt', color_border)
                for j in range(days):
                    if not week_events[j]:
                        # no events today
                        self.printer.msg(
                                empty_day + self.printer.art['vrt'],
                                color_border
                        )
                        continue

                    curr_event = week_events[j][0]
                    print_len, cut_idx = self._get_cut_index(curr_event.title)
                    padding = ' ' * (self.options['cal_width'] - print_len)

                    self.printer.msg(
                            curr_event.title[:cut_idx] + padding,
                            curr_event.color
                    )

                    # trim what we've already printed
                    trimmed_title = curr_event.title[cut_idx:].strip()

                    if trimmed_title == '':
                        week_events[j].pop(0)
                    else:
                        week_events[j][0] = \
                                curr_event._replace(title=trimmed_title)

                    done = False
                    self.printer.art_msg('vrt', color_border)

                self.printer.msg('\n')
                if done:
                    break

            if i < range(count)[len(range(count)) - 1]:
                self.printer.msg(week_divider + '\n', color_border)
            else:
                self.printer.msg(week_bottom + '\n', color_border)

    def _tsv(self, start_datetime, event_list):
        for event in event_list:
            if self.options['ignore_started'] and (event['s'] < self.now):
                continue
            if self.options['ignore_declined'] and self._DeclinedEvent(event):
                continue
            output = '%s\t%s\t%s\t%s' % (event['s'].strftime('%Y-%m-%d'),
                                         event['s'].strftime('%H:%M'),
                                         event['e'].strftime('%Y-%m-%d'),
                                         event['e'].strftime('%H:%M'))

            if self.details.get('url'):
                output += '\t%s' % (event['htmlLink']
                                    if 'htmlLink' in event else '')
                output += '\t%s' % (event['hangoutLink']
                                    if 'hangoutLink' in event else '')

            if self.details.get('conference'):
                conference_data = (event['conferenceData']
                                   if 'conferenceData' in event else None)

                # only display first entry point for TSV
                # https://github.com/insanum/gcalcli/issues/533
                entry_point = (conference_data['entryPoints'][0]
                               if conference_data is not None else None)

                output += '\t%s' % (entry_point['entryPointType']
                                    if conference_data is not None else '')

                output += '\t%s' % (entry_point['uri']
                                    if conference_data is not None else '')

            output += '\t%s' % self._valid_title(event).strip()

            if self.details.get('location'):
                output += '\t%s' % (event['location'].strip()
                                    if 'location' in event else '')

            if self.details.get('description'):
                output += '\t%s' % (event['description'].strip()
                                    if 'description' in event else '')

            if self.details.get('calendar'):
                output += '\t%s' % event['gcalcli_cal']['summary'].strip()

            if self.details.get('email'):
                output += '\t%s' % (event['creator']['email'].strip()
                                    if 'email' in event['creator'] else '')

            output = '%s\n' % output.replace('\n', '''\\n''')
            sys.stdout.write(output)

    def _PrintEvent(self, event, prefix):

        def _format_descr(descr, indent, box):
            wrapper = textwrap.TextWrapper()
            if box:
                wrapper.initial_indent = (indent + '  ')
                wrapper.subsequent_indent = (indent + '  ')
                wrapper.width = (self.details.get('width') - 2)
            else:
                wrapper.initial_indent = indent
                wrapper.subsequent_indent = indent
                wrapper.width = self.details.get('width')
            new_descr = ''
            for line in descr.split('\n'):
                if box:
                    tmp_line = wrapper.fill(line)
                    for single_line in tmp_line.split('\n'):
                        single_line = single_line.ljust(
                                self.details.get('width'), ' '
                        )
                        new_descr += single_line[:len(indent)] + \
                            self.printer.art['vrt'] + \
                            single_line[(len(indent) + 1):
                                        (self.details.get('width') - 1)] + \
                            self.printer.art['vrt'] + '\n'
                else:
                    new_descr += wrapper.fill(line) + '\n'
            return new_descr.rstrip()

        indent = 10 * ' '
        details_indent = 19 * ' '

        if not prefix:
            prefix = indent
        self.printer.msg(prefix, self.options['color_date'])

        happening_now = event['s'] <= self.now <= event['e']
        all_day = self._isallday(event)
        if self.options['override_color'] and event.get('colorId'):
            if happening_now and not all_day:
                event_color = self.options['color_now_marker']
            else:
                event_color = self._calendar_color(event, override_color=True)
        else:
            event_color = self.options['color_now_marker'] \
                if happening_now and not all_day \
                else self._calendar_color(event)

        time_width = '%-5s' if self.options['military'] else '%-7s'
        if all_day:
            fmt = '  ' + time_width + '  %s\n'
            self.printer.msg(
                    fmt % ('', self._valid_title(event).strip()),
                    event_color
            )
        else:
            tmp_start_time_str = \
                utils.agenda_time_fmt(event['s'], self.options['military'])
            tmp_end_time_str = ''
            fmt = '  ' + time_width + '   ' + time_width + '  %s\n'

            if self.details.get('end'):
                tmp_end_time_str = \
                    utils.agenda_time_fmt(event['e'], self.options['military'])
                fmt = '  ' + time_width + ' - ' + time_width + '  %s\n'

            self.printer.msg(
                    fmt % (tmp_start_time_str, tmp_end_time_str,
                           self._valid_title(event).strip()),
                    event_color
            )

        if self.details.get('calendar'):
            xstr = '%s  Calendar: %s\n' % (
                    details_indent, event['gcalcli_cal']['summary']
            )
            self.printer.msg(xstr, 'default')

        if self.details.get('url') and 'htmlLink' in event:
            hlink = event['htmlLink']
            xstr = '%s  Link: %s\n' % (details_indent, hlink)
            self.printer.msg(xstr, 'default')

        if self.details.get('url') and 'hangoutLink' in event:
            hlink = event['hangoutLink']
            xstr = '%s  Hangout Link: %s\n' % (details_indent, hlink)
            self.printer.msg(xstr, 'default')

        if self.details.get('conference') and 'conferenceData' in event:
            for entry_point in event['conferenceData']['entryPoints']:
                entry_point_type = entry_point['entryPointType']
                hlink = entry_point['uri']
                xstr = '%s  Conference Link: %s: %s\n' % (details_indent,
                                                          entry_point_type,
                                                          hlink)
                self.printer.msg(xstr, 'default')

        if self.details.get('location') \
                and 'location' in event \
                and event['location'].strip():
            xstr = '%s  Location: %s\n' % (
                details_indent,
                event['location'].strip()
            )
            self.printer.msg(xstr, 'default')

        if self.details.get('attendees') and 'attendees' in event:
            xstr = '%s  Attendees:\n' % (details_indent)
            self.printer.msg(xstr, 'default')

            if 'self' not in event['organizer']:
                xstr = '%s    %s: <%s>\n' % (
                    details_indent,
                    event['organizer'].get('displayName', 'Not Provided')
                                      .strip(),
                    event['organizer'].get('email', 'Not Provided').strip()
                )
                self.printer.msg(xstr, 'default')

            for attendee in event['attendees']:
                if 'self' not in attendee:
                    xstr = '%s    %s: <%s>\n' % (
                        details_indent,
                        attendee.get('displayName', 'Not Provided').strip(),
                        attendee.get('email', 'Not Provided').strip()
                    )
                    self.printer.msg(xstr, 'default')

        if self.details.get('attachments') and 'attachments' in event:
            xstr = '%s  Attachments:\n' % (details_indent)
            self.printer.msg(xstr, 'default')

            for attendee in event['attachments']:
                xstr = '%s    %s\n%s    -> %s\n' % (
                    details_indent,
                    attendee.get('title', 'Not Provided').strip(),
                    details_indent,
                    attendee.get('fileUrl', 'Not Provided').strip()
                )
                self.printer.msg(xstr, 'default')

        if self.details.get('length'):
            diff_date_time = (event['e'] - event['s'])
            xstr = '%s  Length: %s\n' % (details_indent, diff_date_time)
            self.printer.msg(xstr, 'default')

        if self.details.get('reminders') and 'reminders' in event:
            if event['reminders']['useDefault'] is True:
                xstr = '%s  Reminder: (default)\n' % (details_indent)
                self.printer.msg(xstr, 'default')
            elif 'overrides' in event['reminders']:
                for rem in event['reminders']['overrides']:
                    xstr = '%s  Reminder: %s %d minutes\n' % \
                           (details_indent, rem['method'], rem['minutes'])
                    self.printer.msg(xstr, 'default')

        if self.details.get('email') \
                and 'email' in event['creator'] \
                and event['creator']['email'].strip():
            xstr = '%s  Email: %s\n' % (
                details_indent,
                event['creator']['email'].strip()
            )
            self.printer.msg(xstr, 'default')

        if self.details.get('description') \
                and 'description' in event \
                and event['description'].strip():
            descr_indent = details_indent + '  '
            box = True  # leave old non-box code for option later
            if box:
                top_marker = (
                        descr_indent +
                        self.printer.art['ulc'] +
                        (self.printer.art['hrz'] *
                            ((self.details.get('width') - len(descr_indent))
                             - 2
                             )
                         ) +
                        self.printer.art['urc']
                )
                bot_marker = (
                        descr_indent +
                        self.printer.art['llc'] +
                        (self.printer.art['hrz'] *
                            ((self.details.get('width') - len(descr_indent))
                             - 2
                             )
                         ) +
                        self.printer.art['lrc']
                )
                xstr = '%s  Description:\n%s\n%s\n%s\n' % (
                    details_indent,
                    top_marker,
                    _format_descr(event['description'].strip(),
                                  descr_indent, box),
                    bot_marker
                )
            else:
                marker = descr_indent + '-' * \
                    (self.details.get('width') - len(descr_indent))
                xstr = '%s  Description:\n%s\n%s\n%s\n' % (
                    details_indent,
                    marker,
                    _format_descr(event['description'].strip(),
                                  descr_indent, box),
                    marker
                )
            self.printer.msg(xstr, 'default')

    def _delete_event(self, event):

        if self.expert:
            self._retry_with_backoff(
                self.get_cal_service()
                    .events()
                    .delete(
                        calendarId=event['gcalcli_cal']['id'],
                        eventId=event['id']
                    )
            )
            self.printer.msg('Deleted!\n', 'red')
            return

        self.printer.msg('Delete? [N]o [y]es [q]uit: ', 'magenta')
        val = input()

        if not val or val.lower() == 'n':
            return

        elif val.lower() == 'y':
            self._retry_with_backoff(
                self.get_cal_service()
                    .events()
                    .delete(
                        calendarId=event['gcalcli_cal']['id'],
                        eventId=event['id']
                    )
            )
            self.printer.msg('Deleted!\n', 'red')

        elif val.lower() == 'q':
            sys.stdout.write('\n')
            sys.exit(0)

        else:
            self.printer.err_msg('Error: invalid input\n')
            sys.stdout.write('\n')
            sys.exit(1)

    def _SetEventStartEnd(self, start, end, event):
        event['s'] = parse(start)
        event['e'] - parse(end)

        if self.options.get('allday'):
            event['start'] = {'date': start,
                              'dateTime': None,
                              'timeZone': None}
            event['end'] = {'date': end,
                            'dateTime': None,
                            'timeZone': None}
        else:
            event['start'] = {'date': None,
                              'dateTime': start,
                              'timeZone': event['gcalcli_cal']['timeZone']}
            event['end'] = {'date': None,
                            'dateTime': end,
                            'timeZone': event['gcalcli_cal']['timeZone']}
        return event

    def _edit_event(self, event):

        while True:
            self.printer.msg(
                    'Edit?\n[N]o [s]ave [q]uit [t]itle [l]ocation [w]hen ' +
                    'len[g]th [r]eminder [c]olor [d]escr: ', 'magenta'
            )
            val = input()

            if not val or val.lower() == 'n':
                return

            elif val.lower() == 'c':
                val = get_input(self.printer, 'Color: ', VALID_COLORS)
                if val:
                    self.options['override_color'] = True
                    event['colorId'] = get_override_color_id(val)

            elif val.lower() == 's':
                # copy only editable event details for patching
                mod_event = {}
                keys = ['summary', 'location', 'start', 'end', 'reminders',
                        'description', 'colorId']
                for k in keys:
                    if k in event:
                        mod_event[k] = event[k]

                self._retry_with_backoff(
                    self.get_cal_service()
                        .events()
                        .patch(
                            calendarId=event['gcalcli_cal']['id'],
                            eventId=event['id'],
                            body=mod_event
                        )
                )
                self.printer.msg('Saved!\n', 'red')
                return

            elif not val or val.lower() == 'q':
                sys.stdout.write('\n')
                sys.exit(0)

            elif val.lower() == 't':
                val = get_input(self.printer, 'Title: ', STR_NOT_EMPTY)
                if val.strip():
                    event['summary'] = val.strip()

            elif val.lower() == 'l':
                val = get_input(self.printer, 'Location: ', STR_ALLOW_EMPTY)
                if val.strip():
                    event['location'] = val.strip()

            elif val.lower() == 'w':
                val = get_input(self.printer, 'When: ', PARSABLE_DATE).strip()
                if val:
                    td = (event['e'] - event['s'])
                    length = ((td.days * 1440) + (td.seconds / 60))
                    all_day = self.options.get('allday')
                    try:
                        new_start, new_end = utils.get_times_from_duration(
                                val, length, all_day
                        )
                    except ValueError as exc:
                        self.printer.err_msg(str(exc))
                        sys.exit(1)
                    event = self._SetEventStartEnd(new_start, new_end, event)

            elif val.lower() == 'g':
                val = get_input(
                        self.printer, 'Length (mins or human readable): ',
                        PARSABLE_DURATION
                )
                if val:
                    all_day = self.options.get('allday')
                try:
                    new_start, new_end = utils.get_times_from_duration(
                            event['start']['dateTime'], val,
                            all_day
                    )
                    event = self._SetEventStartEnd(new_start, new_end, event)
                except ValueError as exc:
                    self.printer.err_msg(str(exc))

            elif val.lower() == 'r':
                rem = []
                while True:
                    r = get_input(
                            self.printer, "Enter a valid reminder or '.' to"
                                          "end: ", REMINDER
                    )
                    if r == '.':
                        break
                    rem.append(r)

                if rem or not self.options['default_reminders']:
                    event['reminders'] = {'useDefault': False,
                                          'overrides': []}
                    for r in rem:
                        n, m = utils.parse_reminder(r)
                        event['reminders']['overrides'].append({'minutes': n,
                                                                'method': m})
                else:
                    event['reminders'] = {'useDefault': True,
                                          'overrides': []}

            elif val.lower() == 'd':
                val = get_input(self.printer, 'Description: ', STR_ALLOW_EMPTY)
                if val.strip():
                    event['description'] = val.strip()

            else:
                self.printer.err_msg('Error: invalid input\n')
                sys.stdout.write('\n')
                sys.exit(1)

            self._PrintEvent(
                    event, event['s'].strftime('\n%Y-%m-%d')
            )

    def _iterate_events(self, start_datetime, event_list, year_date=False,
                        work=None):

        selected = 0

        if len(event_list) == 0:
            self.printer.msg('\nNo Events Found...\n', 'yellow')
            return selected

        # 10 chars for day and length must match 'indent' in _PrintEvent
        day_format = '\n%Y-%m-%d' if year_date else '\n%a %b %d'
        day = ''

        for event in event_list:
            if self.options['ignore_started'] and (event['s'] < self.now):
                continue
            if self.options['ignore_declined'] and self._DeclinedEvent(event):
                continue

            selected += 1
            tmp_day_str = event['s'].strftime(day_format)
            prefix = None
            if year_date or tmp_day_str != day:
                day = prefix = tmp_day_str

            self._PrintEvent(event, prefix)

            if work:
                work(event)

        return selected

    def _GetAllEvents(self, cal, events, end):

        event_list = []

        while 1:
            if 'items' not in events:
                break

            for event in events['items']:

                event['gcalcli_cal'] = cal

                if 'status' in event and event['status'] == 'cancelled':
                    continue

                if 'dateTime' in event['start']:
                    event['s'] = parse(event['start']['dateTime'])
                else:
                    # all date events
                    event['s'] = parse(event['start']['date'])

                event['s'] = self._localize_datetime(event['s'])

                if 'dateTime' in event['end']:
                    event['e'] = parse(event['end']['dateTime'])
                else:
                    # all date events
                    event['e'] = parse(event['end']['date'])

                event['e'] = self._localize_datetime(event['e'])

                # For all-day events, Google seems to assume that the event
                # time is based in the UTC instead of the local timezone.  Here
                # we filter out those events start beyond a specified end time.
                if end and (event['s'] >= end):
                    continue

                # http://en.wikipedia.org/wiki/Year_2038_problem
                # Catch the year 2038 problem here as the python dateutil
                # module can choke throwing a ValueError exception. If either
                # the start or end time for an event has a year '>= 2038' dump
                # it.
                if event['s'].year >= 2038 or event['e'].year >= 2038:
                    continue

                event_list.append(event)

            pageToken = events.get('nextPageToken')
            if pageToken:
                events = self._retry_with_backoff(
                             self.get_cal_service()
                                 .events()
                                 .list(
                                     calendarId=cal['id'],
                                     pageToken=pageToken
                                 )
                         )
            else:
                break

        return event_list

    def _search_for_events(self, start, end, search_text):

        event_list = []
        for cal in self.cals:
            events = self._retry_with_backoff(
                         self.get_cal_service()
                             .events()
                             .list(
                                 calendarId=cal['id'],
                                 timeMin=start.isoformat() if start else None,
                                 timeMax=end.isoformat() if end else None,
                                 q=search_text if search_text else None,
                                 singleEvents=True
                             )
                    )
            event_list.extend(self._GetAllEvents(cal, events, end))

        event_list.sort(key=lambda x: x['s'])

        return event_list

    def _DeclinedEvent(self, event):
        if 'attendees' in event:
            attendees = [a for a in event['attendees']
                         if a['email'] == event['gcalcli_cal']['id']]
            if attendees and attendees[0]['responseStatus'] == 'declined':
                return True
        return False

    def ListAllCalendars(self):
        access_len = 0

        for cal in self.all_cals:
            length = len(cal['accessRole'])
            if length > access_len:
                access_len = length

        if access_len < len('Access'):
            access_len = len('Access')

        _format = ' %0' + str(access_len) + 's  %s\n'

        self.printer.msg(
                _format % ('Access', 'Title'), self.options['color_title']
        )
        self.printer.msg(
                _format % ('------', '-----'), self.options['color_title']
        )

        for cal in self.all_cals:
            self.printer.msg(
                    _format % (cal['accessRole'], cal['summary']),
                    self._calendar_color(cal)
            )

    def _display_queried_events(self, start, end, search=None,
                                year_date=False):
        event_list = self._search_for_events(start, end, search)

        if self.options.get('tsv'):
            return self._tsv(start, event_list)
        else:
            return self._iterate_events(start, event_list, year_date=year_date)

    def TextQuery(self, search_text='', start=None, end=None):
        if not search_text:
            # the empty string would get *ALL* events...
            raise GcalcliError('Search text is required.')

        return self._display_queried_events(start, end, search_text, True)

    def UpdatesQuery(self, last_updated_datetime, start=None, end=None):
        if not start:
            start = self.now.replace(hour=0, minute=0, second=0, microsecond=0)

        if not end:
            end = (start + relativedelta(months=+1)).replace(day=1)

        event_list = self._search_for_events(start, end, None)
        event_list = [e for e in event_list
                      if (utils.get_time_from_str(e['updated']) >=
                          last_updated_datetime)]
        print("Updates since:",
              last_updated_datetime,
              "events starting",
              start,
              "until",
              end)
        return self._iterate_events(start, event_list, year_date=False)

    def ConflictsQuery(self, search_text='', start=None, end=None):
        if not start:
            start = self.now.replace(hour=0, minute=0, second=0, microsecond=0)

        if not end:
            end = (start + timedelta(days=self.conflicts_lookahead_days))

        event_list = self._search_for_events(start, end, search_text)
        show_conflicts = ShowConflicts(
                            lambda e: self._PrintEvent(e, "\t !!! Conflict: "))

        return self._iterate_events(start,
                                    event_list,
                                    year_date=False,
                                    work=show_conflicts.show_conflicts)

    def AgendaQuery(self, start=None, end=None):
        if not start:
            start = self.now.replace(hour=0, minute=0, second=0, microsecond=0)

        if not end:
            end = (start + timedelta(days=self.agenda_length))

        return self._display_queried_events(start, end)

    def CalQuery(self, cmd, start_text='', count=1):
        if not start_text:
            # convert now to midnight this morning and use for default
            start = self.now.replace(hour=0,
                                     minute=0,
                                     second=0,
                                     microsecond=0)
        else:
            try:
                start = utils.get_time_from_str(start_text)
                start = start.replace(hour=0, minute=0, second=0,
                                      microsecond=0)
            except Exception:
                self.printer.err_msg('Error: failed to parse start time\n')
                return

        # convert start date to the beginning of the week or month
        if cmd == 'calw':
            day_num = self._cal_monday(int(start.strftime('%w')))
            start = (start - timedelta(days=day_num))
            end = (start + timedelta(days=(count * 7)))
        else:  # cmd == 'calm':
            start = (start - timedelta(days=(start.day - 1)))
            end_month = (start.month + 1)
            end_year = start.year
            if end_month == 13:
                end_month = 1
                end_year += 1
            end = start.replace(month=end_month, year=end_year)
            days_in_month = (end - start).days
            offset_days = int(start.strftime('%w'))
            if self.options['cal_monday']:
                offset_days -= 1
                if offset_days < 0:
                    offset_days = 6
            total_days = (days_in_month + offset_days)
            count = int(total_days / 7)
            if total_days % 7:
                count += 1

        event_list = self._search_for_events(start, end, None)

        self._GraphEvents(cmd, start, count, event_list)

    def QuickAddEvent(self, event_text, reminders=None):
        """Wrapper around Google Calendar API's quickAdd"""
        if not event_text:
            raise GcalcliError('event_text is required for a quickAdd')

        if len(self.cals) != 1:
            # TODO: get a better name for this exception class
            # and use it elsewhere
            raise GcalcliError('You must only specify a single calendar\n')

        new_event = self._retry_with_backoff(
            self.get_cal_service()
                .events()
                .quickAdd(
                    calendarId=self.cals[0]['id'],
                    text=event_text
                )
        )

        if reminders or not self.options['default_reminders']:
            rem = {}
            rem['reminders'] = {'useDefault': False,
                                'overrides': []}
            for r in reminders:
                n, m = utils.parse_reminder(r)
                rem['reminders']['overrides'].append({'minutes': n,
                                                      'method': m})

            new_event = self._retry_with_backoff(
                            self.get_cal_service()
                                .events()
                                .patch(
                                    calendarId=self.cals[0]['id'],
                                    eventId=new_event['id'],
                                    body=rem
                                )
                        )

        if self.details.get('url'):
            hlink = new_event['htmlLink']
            self.printer.msg('New event added: %s\n' % hlink, 'green')

        return new_event

    def AddEvent(self, title, where, start, end, descr, who, reminders, color):

        if len(self.cals) != 1:
            # Calendar not specified. Prompt the user to select it
            writers = (self.ACCESS_OWNER, self.ACCESS_WRITER)
            cals_with_write_perms = [cal for cal in self.cals
                                     if cal['accessRole'] in writers]

            cal_names_with_idx = []
            for idx, cal in enumerate(cals_with_write_perms):
                cal_names_with_idx.append(str(idx) + ' ' + cal['summary'])
            cal_names_with_idx = '\n'.join(cal_names_with_idx)
            print(cal_names_with_idx)
            val = get_input(self.printer, 'Specify calendar from above: ',
                            STR_TO_INT)
            try:
                self.cals = [cals_with_write_perms[int(val)]]
            except IndexError:
                raise GcalcliError('The entered number doesn\'t appear on the '
                                   'list above\n')

        event = {}
        event['summary'] = title

        if self.options['allday']:
            event['start'] = {'date': start}
            event['end'] = {'date': end}

        else:
            event['start'] = {'dateTime': start,
                              'timeZone': self.cals[0]['timeZone']}
            event['end'] = {'dateTime': end,
                            'timeZone': self.cals[0]['timeZone']}

        if where:
            event['location'] = where
        if descr:
            event['description'] = descr

        if color:
            event['colorId'] = get_override_color_id(color)

        event['attendees'] = list(map(lambda w: {'email': w}, who))

        event = self._add_reminders(event, reminders)
        events = self.get_cal_service().events()
        request = events.insert(calendarId=self.cals[0]['id'], body=event)
        new_event = self._retry_with_backoff(request)

        if self.details.get('url'):
            hlink = new_event['htmlLink']
            self.printer.msg('New event added: %s\n' % hlink, 'green')

        return new_event

    def ModifyEvents(self, work, search_text, start=None, end=None,
                     expert=False):
        if not search_text:
            raise GcalcliError('The empty string would get *ALL* events')

        event_list = self._search_for_events(start, end, search_text)
        self.expert = expert
        return self._iterate_events(
                self.now, event_list, year_date=True, work=work)

    def Remind(self, minutes, command, use_reminders=False):
        """
        Check for events between now and now+minutes.

        If use_reminders then only remind if now >= event['start'] - reminder
        """

        # perform a date query for now + minutes + slip
        start = self.now
        end = (start + timedelta(minutes=(minutes + 5)))

        event_list = self._search_for_events(start, end, None)

        message = ''

        for event in event_list:

            # skip this event if it already started
            # XXX maybe add a 2+ minute grace period here...
            if event['s'] < self.now:
                continue

            # not sure if 'reminders' always in event
            if use_reminders and 'reminders' in event \
                    and 'overrides' in event['reminders']:
                if all(event['s'] - timedelta(minutes=r['minutes']) > self.now
                        for r in event['reminders']['overrides']):
                    # don't remind if all reminders haven't arrived yet
                    continue

            if self.options.get('military'):
                tmp_time_str = event['s'].strftime('%H:%M')
            else:
                tmp_time_str = \
                    event['s'].strftime('%I:%M').lstrip('0') + \
                    event['s'].strftime('%p').lower()

            message += '%s  %s\n' % \
                       (tmp_time_str, self._valid_title(event).strip())

        if not message:
            return

        cmd = shlex.split(command)

        for i, a in zip(range(len(cmd)), cmd):
            if a == '%s':
                cmd[i] = message

        pid = os.fork()
        if not pid:
            os.execvp(cmd[0], cmd)

    def ImportICS(self, verbose=False, dump=False, reminders=None,
                  icsFile=None):

        def CreateEventFromVOBJ(ve):

            event = {}

            if verbose:
                print('+----------------+')
                print('| Calendar Event |')
                print('+----------------+')

            if hasattr(ve, 'summary'):
                if verbose:
                    print('Event........%s' % ve.summary.value)
                event['summary'] = ve.summary.value

            if hasattr(ve, 'location'):
                if verbose:
                    print('Location.....%s' % ve.location.value)
                event['location'] = ve.location.value

            if not hasattr(ve, 'dtstart') or not hasattr(ve, 'dtend'):
                self.printer.err_msg(
                        'Error: event does not have a dtstart and dtend!\n'
                )
                return None

            if verbose:
                if ve.dtstart.value:
                    print('Start........%s' % ve.dtstart.value.isoformat())
                if ve.dtend.value:
                    print('End..........%s' % ve.dtend.value.isoformat())
                if ve.dtstart.value:
                    print('Local Start..%s' %
                          self._localize_datetime(ve.dtstart.value)
                          )
                if ve.dtend.value:
                    print('Local End....%s' %
                          self._localize_datetime(ve.dtend.value)
                          )

            if hasattr(ve, 'rrule'):
                if verbose:
                    print('Recurrence...%s' % ve.rrule.value)

                event['recurrence'] = ['RRULE:' + ve.rrule.value]

            if hasattr(ve, 'dtstart') and ve.dtstart.value:
                # XXX
                # Timezone madness! Note that we're using the timezone for the
                # calendar being added to. This is OK if the event is in the
                # same timezone. This needs to be changed to use the timezone
                # from the DTSTART and DTEND values. Problem is, for example,
                # the TZID might be "Pacific Standard Time" and Google expects
                # a timezone string like "America/Los_Angeles". Need to find a
                # way in python to convert to the more specific timezone
                # string.
                # XXX
                # print ve.dtstart.params['X-VOBJ-ORIGINAL-TZID'][0]
                # print self.cals[0]['timeZone']
                # print dir(ve.dtstart.value.tzinfo)
                # print vars(ve.dtstart.value.tzinfo)

                start = ve.dtstart.value.isoformat()
                if isinstance(ve.dtstart.value, datetime):
                    event['start'] = {'dateTime': start,
                                      'timeZone': self.cals[0]['timeZone']}
                else:
                    event['start'] = {'date': start}

                event = self._add_reminders(event, reminders)

                # Can only have an end if we have a start, but not the other
                # way around apparently...  If there is no end, use the start
                if hasattr(ve, 'dtend') and ve.dtend.value:
                    end = ve.dtend.value.isoformat()
                    if isinstance(ve.dtend.value, datetime):
                        event['end'] = {'dateTime': end,
                                        'timeZone': self.cals[0]['timeZone']}
                    else:
                        event['end'] = {'date': end}

                else:
                    event['end'] = event['start']

            if hasattr(ve, 'description') and ve.description.value.strip():
                descr = ve.description.value.strip()
                if verbose:
                    print('Description:\n%s' % descr)
                event['description'] = descr

            if hasattr(ve, 'organizer'):
                if ve.organizer.value.startswith('MAILTO:'):
                    email = ve.organizer.value[7:]
                else:
                    email = ve.organizer.value
                if verbose:
                    print('organizer:\n %s' % email)
                event['organizer'] = {'displayName': ve.organizer.name,
                                      'email': email}

            if hasattr(ve, 'attendee_list'):
                if verbose:
                    print('attendees:')
                event['attendees'] = []
                for attendee in ve.attendee_list:
                    if attendee.value.upper().startswith('MAILTO:'):
                        email = attendee.value[7:]
                    else:
                        email = attendee.value
                    if verbose:
                        print(' %s' % email)

                    event['attendees'].append({'displayName': attendee.name,
                                               'email': email})

            return event

        try:
            import vobject
        except ImportError:
            self.printer.err_msg(
                    'Python vobject module not installed!\n'
            )
            sys.exit(1)

        if dump:
            verbose = True

        if not dump and len(self.cals) != 1:
            raise GcalcliError('Must specify a single calendar\n')

        f = sys.stdin

        if icsFile:
            try:
                f = icsFile
            except Exception as e:
                self.printer.err_msg('Error: ' + str(e) + '!\n')
                sys.exit(1)

        while True:
            try:
                v = next(vobject.readComponents(f))
            except StopIteration:
                break

            for ve in v.vevent_list:
                event = CreateEventFromVOBJ(ve)

                if not event:
                    continue

                if dump:
                    continue

                if not verbose:
                    new_event = self._retry_with_backoff(
                                    self.get_cal_service()
                                        .events()
                                        .insert(
                                            calendarId=self.cals[0]['id'],
                                            body=event
                                        )
                                )
                    hlink = new_event.get('htmlLink')
                    self.printer.msg(
                            'New event added: %s\n' % hlink, 'green'
                    )
                    continue

                self.printer.msg('\n[S]kip [i]mport [q]uit: ', 'magenta')
                val = input()
                if not val or val.lower() == 's':
                    continue
                if val.lower() == 'i':
                    new_event = self._retry_with_backoff(
                                    self.get_cal_service()
                                        .events()
                                        .insert(
                                            calendarId=self.cals[0]['id'],
                                            body=event
                                        )
                                )
                    hlink = new_event.get('htmlLink')
                    self.printer.msg('New event added: %s\n' % hlink, 'green')
                elif val.lower() == 'q':
                    sys.exit(0)
                else:
                    self.printer.err_msg('Error: invalid input\n')
                    sys.exit(1)
        # TODO: return the number of events added
        return True
