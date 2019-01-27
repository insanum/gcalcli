#!/usr/bin/env python

# ** The MIT License **
#
# Copyright (c) 2007 Eric Davis (aka Insanum)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Dude... just buy us a beer. :-)
#

# XXX Todo/Cleanup XXX
# threading is currently broken when getting event list
# if threading works then move pageToken processing from GetAllEvents to thread
# support different types of reminders plus multiple ones (popup, sms, email)
# add caching, should be easy (dump all calendar JSON data to file)
# add support for multiline description input in the 'add' and 'edit' commands
# maybe add support for freebusy ?

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
# Author: Eric Davis <http://www.insanum.com>                               #
#         Brian Hartvigsen <http://github.com/tresni>                       #
#         Joshua Crowgey                                                    #
# Home: https://github.com/insanum/gcalcli                                  #
#                                                                           #
# Everything you need to know (Google API Calendar v3): http://goo.gl/HfTGQ #
#                                                                           #
#############################################################################
from __future__ import print_function, absolute_import

# These are standard libraries and should never fail
import sys
import os
import re
import shlex
import time
import textwrap
import signal
import json
import random
from datetime import datetime, timedelta, date
from unicodedata import east_asian_width
from collections import namedtuple

from gcalcli.validators import (
    get_input, get_override_color_id, STR_NOT_EMPTY, PARSABLE_DATE, STR_TO_INT,
    VALID_COLORS, STR_ALLOW_EMPTY, REMINDER)

# Required 3rd party libraries
try:
    from dateutil.tz import tzlocal
    from dateutil.parser import parse
    import httplib2
    from six import next
    from six.moves import input, range, zip, map, cPickle as pickle
    from apiclient.discovery import build
    from apiclient.errors import HttpError
    from oauth2client.file import Storage
    from oauth2client.client import OAuth2WebServerFlow
    from oauth2client import tools
except ImportError as exc:  # pragma: no cover
    print("ERROR: Missing module - %s" % exc.args[0])
    sys.exit(1)


# Package local imports

from gcalcli import __program__, __version__
from gcalcli import utils

from gcalcli.argparsers import get_argument_parser
from gcalcli.utils import _u, days_since_epoch
from gcalcli.printer import Printer, valid_color_name
from gcalcli.exceptions import GcalcliError


EventTitle = namedtuple('EventTitle', ['title', 'color'])
CalName = namedtuple('CalName', ['name', 'color'])


class GoogleCalendarInterface:

    cache = {}
    allCals = []
    allEvents = []
    now = datetime.now(tzlocal())
    agenda_length = 5
    maxRetries = 5
    authHttp = None
    calService = None
    urlService = None

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
            self.cals = self.allCals
            return

        for cal_name in selected_names:
            matches = []
            for self_cal in self.allCals:
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
        for n in range(0, self.maxRetries):
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
        if not self.authHttp:
            if self.options['configFolder']:
                storage = Storage(
                        os.path.expanduser(
                            "%s/oauth" % self.options['configFolder']))
            else:
                storage = Storage(os.path.expanduser('~/.gcalcli_oauth'))
            credentials = storage.get()

            if credentials is None or credentials.invalid:
                credentials = tools.run_flow(
                    OAuth2WebServerFlow(
                        client_id=self.options['client_id'],
                        client_secret=self.options['client_secret'],
                        scope=['https://www.googleapis.com/auth/calendar',
                               'https://www.googleapis.com/auth/urlshortener'],
                        user_agent=__program__ + '/' + __version__),
                    storage,
                    Namespace(**self.options))

            self.authHttp = credentials.authorize(httplib2.Http())

        return self.authHttp

    def _cal_service(self):
        if not self.calService:
            self.calService = \
                build(serviceName='calendar',
                      version='v3',
                      http=self._google_auth())

        return self.calService

    def _url_service(self):
        if not self.urlService:
            self._google_auth()
            self.urlService = \
                build(serviceName='urlshortener',
                      version='v1',
                      http=self._google_auth())

        return self.urlService

    def _get_cached(self):
        if self.options['configFolder']:
            cacheFile = os.path.expanduser(
                    "%s/cache" % self.options['configFolder'])
        else:
            cacheFile = os.path.expanduser('~/.gcalcli_cache')

        if self.options['refresh_cache']:
            try:
                os.remove(cacheFile)
            except OSError:
                pass
                # fall through

        self.cache = {}
        self.allCals = []

        if self.options['use_cache']:
            # note that we need to use pickle for cache data since we stuff
            # various non-JSON data in the runtime storage structures
            try:
                with open(cacheFile, 'rb') as _cache_:
                    self.cache = pickle.load(_cache_)
                    self.allCals = self.cache['allCals']
                # XXX assuming data is valid, need some verification check here
                return
            except IOError:
                pass
                # fall through

        calList = self._retry_with_backoff(
            self._cal_service().calendarList().list())

        while True:
            for cal in calList['items']:
                self.allCals.append(cal)
            pageToken = calList.get('nextPageToken')
            if pageToken:
                calList = self._retry_with_backoff(
                    self._cal_service().calendarList().list(
                        pageToken=pageToken))
            else:
                break

        self.allCals.sort(key=lambda x: x['accessRole'])

        if self.options['use_cache']:
            self.cache['allCals'] = self.allCals
            with open(cacheFile, 'wb') as _cache_:
                pickle.dump(self.cache, _cache_)

    def _shorten_url(self, url):
        if self.details.get('url', False) != "short":
            return url
        # Note that when authenticated to a google account different shortUrls
        # can be returned for the same longUrl. See: http://goo.gl/Ya0A9
        shortUrl = self._retry_with_backoff(
            self._url_service().url().insert(body={'longUrl': url}))
        return shortUrl['id']

    def _calendar_color(self, event, override_color=False):
        ansi_codes = {
            "1": "brightblue",
            "2": "brightgreen",
            "3": "brightmagenta",
            "4": "magenta",
            "5": "brightyellow",
            "6": "brightred",
            "7": "brightcyan",
            "8": "brightblack",
            "9": "blue",
            "10": "green",
            "11": "red"
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
            return "(No title)"

    def _isallday(self, event):
        return event['s'].hour == 0 and event['s'].minute == 0 and \
            event['e'].hour == 0 and event['e'].minute == 0

    def _cal_monday(self, day_num):
        """Shift the day number if we're doing cal monday, or cal_weekend is
        false, since that also means we're starting on day 1"""
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
            return ' '.join([event['s'].strftime("%H:%M"), titlestr])
        else:
            return ' '.join([event['s'].strftime("%I:%M").lstrip('0') +
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
        if self.now < start_dt or self.now > end_dt:
            now_in_week = False

        for event in event_list:
            event_daynum = self._cal_monday(int(event['s'].strftime("%w")))
            event_allday = self._isallday(event)

            event_end_date = event['e']
            if event_allday:
                # NOTE(slwaqo): in allDay events end date is always set as
                # day+1 and hour 0:00 so to not display it one day more, it's
                # necessary to lower it by one day
                event_end_date = event['e'] - timedelta(days=1)

            event_is_today = self._event_time_in_range(
                event['s'], start_dt, end_dt)

            event_continues_today = self._event_spans_time(
                event['s'], event_end_date, start_dt)

            # NOTE(slawqo): it's necessary to process events which starts in
            # current period of time but for all day events also to process
            # events which was started before current period of time and are
            # still continue in current period of time
            if event_is_today or (event_allday and event_continues_today):
                force_now_marker = False

                if now_in_week:
                    if (days_since_epoch(self.now) <
                            days_since_epoch(event['s'])):
                        force_now_marker = False
                        week_events[event_daynum - 1].append(
                            EventTitle(
                                '\n' + self.options['cal_width'] * '-',
                                self.options['color_now_marker']))

                    elif self.now <= event['s']:
                        # add a line marker before next event
                        force_now_marker = False
                        week_events[event_daynum].append(
                            EventTitle(
                                '\n' + self.options['cal_width'] * '-',
                                self.options['color_now_marker']))

                    # We don't want to recolor all day events, but ignoring
                    # them leads to issues where the "now" marker misprints
                    # into the wrong day.  This resolves the issue by skipping
                    # all day events for specific coloring but not for previous
                    # or next events
                    elif self.now >= event['s'] and \
                            self.now <= event_end_date and \
                            not event_allday:
                        # line marker is during the event (recolor event)
                        force_now_marker = True

                if force_now_marker:
                    event_color = self.options['color_now_marker']
                else:
                    if self.options['override_color'] and event.get('colorId'):
                        event_color = self._calendar_color(
                            event, override_color=True)
                    else:
                        event_color = self._calendar_color(
                            event)

                # NOTE(slawqo): for all day events it's necessary to add event
                # to more than one day in week_events
                titlestr = self._format_title(event, allday=event_allday)
                if event_allday and event['s'] < event_end_date:
                    if event_end_date > end_dt:
                        end_daynum = 6
                    else:
                        end_daynum = \
                            self._cal_monday(
                                    int(event_end_date.strftime("%w")))
                    if event_daynum > end_daynum:
                        event_daynum = 0
                    for day in range(event_daynum, end_daynum + 1):
                        week_events[day].append(
                            EventTitle('\n' + titlestr, event_color))
                else:
                    # newline and empty string are the keys to turn off
                    # coloring
                    week_events[event_daynum].append(
                            EventTitle('\n' + titlestr, event_color))
        return week_events

    def _printed_len(self, string):
        # We need to treat everything as unicode for this to actually give
        # us the info we want.  Date string were coming in as `str` type
        # so we convert them to unicode and then check their size. Fixes
        # the output issues we were seeing around non-US locale strings
        return sum(
                self.UNIWIDTH[east_asian_width(char)] for char in _u(string))

    def _word_cut(self, word):
        stop = 0
        for i, char in enumerate(word):
            stop += self._printed_len(char)
            if stop >= self.options['cal_width']:
                return stop, i + 1

    def _next_cut(self, string, cur_print_len):
        print_len = 0

        words = _u(string).split()
        for i, word in enumerate(words):
            word_len = self._printed_len(word)
            if (cur_print_len + word_len + print_len) >= \
                    self.options['cal_width']:
                cut_idx = len(' '.join(words[:i]))
                # if the first word is too long, we cannot cut between words
                if cut_idx == 0:
                    return self._word_cut(word)
                return (print_len, cut_idx)
            print_len += word_len + i  # +i for the space between words
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
            return self._next_cut(event_string, 0)

    def _GraphEvents(self, cmd, startDateTime, count, eventList):
        # ignore started events (i.e. events that start previous day and end
        # start day)

        color_border = self.options['color_border']

        while (len(eventList) and eventList[0]['s'] < startDateTime):
            eventList = eventList[1:]

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
                self.printer.art[right])

        week_top = build_divider('ulc', 'ute', 'urc')
        week_divider = build_divider('lte', 'crs', 'rte')
        week_bottom = build_divider('llc', 'bte', 'lrc')
        empty_day = self.options['cal_width'] * ' '

        if cmd == 'calm':
            # month titlebar
            month_title_top = build_divider('ulc', 'hrz', 'urc')
            self.printer.msg(month_title_top + '\n', color_border)

            month_title = startDateTime.strftime('%B %Y')
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
                    self.options['cal_width'] - self._printed_len(day_name))

            self.printer.msg(day_name, self.options['color_date'])
            self.printer.art_msg('vrt', color_border)

        self.printer.msg('\n' + week_divider + '\n', color_border)
        cur_month = startDateTime.strftime("%b")

        # get date range objects for the first week
        if cmd == 'calm':
            day_num = self._cal_monday(int(startDateTime.strftime("%w")))
            startDateTime = (startDateTime - timedelta(days=day_num))
        startWeekDateTime = startDateTime
        endWeekDateTime = (startWeekDateTime + timedelta(days=7))

        for i in range(count):
            # create and print the date line for a week
            for j in range(days):
                if cmd == 'calw':
                    d = (startWeekDateTime +
                         timedelta(days=j)).strftime("%d %b")
                else:  # (cmd == 'calm'):
                    d = (startWeekDateTime +
                         timedelta(days=j)).strftime("%d")
                    if cur_month != (startWeekDateTime +
                                     timedelta(days=j)).strftime("%b"):
                        d = ''
                tmpDateColor = self.options['color_date']

                if self.now.strftime("%d%b%Y") == \
                   (startWeekDateTime + timedelta(days=j)).strftime("%d%b%Y"):
                    tmpDateColor = self.options['color_now_marker']
                    d += " **"

                d += ' ' * (self.options['cal_width'] - self._printed_len(d))

                # print dates
                self.printer.art_msg('vrt', color_border)
                self.printer.msg(d, tmpDateColor)

            self.printer.art_msg('vrt', color_border)
            self.printer.msg('\n')

            week_events = self._get_week_events(
                    startWeekDateTime, endWeekDateTime, eventList)

            # get date range objects for the next week
            startWeekDateTime = endWeekDateTime
            endWeekDateTime = (endWeekDateTime + timedelta(days=7))

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
                                color_border)
                        continue

                    curr_event = week_events[j][0]
                    print_len, cut_idx = self._get_cut_index(curr_event.title)
                    padding = ' ' * (self.options['cal_width'] - print_len)

                    self.printer.msg(
                            curr_event.title[:cut_idx] + padding,
                            curr_event.color)

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

    def _tsv(self, startDateTime, eventList):
        for event in eventList:
            if self.options['ignore_started'] and (event['s'] < self.now):
                continue
            if self.options['ignore_declined'] and self._DeclinedEvent(event):
                continue
            output = "%s\t%s\t%s\t%s" % (_u(event['s'].strftime('%Y-%m-%d')),
                                         _u(event['s'].strftime('%H:%M')),
                                         _u(event['e'].strftime('%Y-%m-%d')),
                                         _u(event['e'].strftime('%H:%M')))

            if self.details.get('url'):
                output += "\t%s" % (self._shorten_url(event['htmlLink'])
                                    if 'htmlLink' in event else '')
                output += "\t%s" % (self._shorten_url(event['hangoutLink'])
                                    if 'hangoutLink' in event else '')

            output += "\t%s" % _u(self._valid_title(event).strip())

            if self.details.get('location'):
                output += "\t%s" % (_u(event['location'].strip())
                                    if 'location' in event else '')

            if self.details.get('description'):
                output += "\t%s" % (_u(event['description'].strip())
                                    if 'description' in event else '')

            if self.details.get('calendar'):
                output += "\t%s" % _u(event['gcalcli_cal']['summary'].strip())

            if self.details.get('email'):
                output += "\t%s" % (event['creator']['email'].strip()
                                    if 'email' in event['creator'] else '')

            output = "%s\n" % output.replace('\n', '''\\n''')
            sys.stdout.write(_u(output))

    def _PrintEvent(self, event, prefix):

        def _formatDescr(descr, indent, box):
            wrapper = textwrap.TextWrapper()
            if box:
                wrapper.initial_indent = (indent + '  ')
                wrapper.subsequent_indent = (indent + '  ')
                wrapper.width = (self.details.get('width') - 2)
            else:
                wrapper.initial_indent = indent
                wrapper.subsequent_indent = indent
                wrapper.width = self.details.get('width')
            new_descr = ""
            for line in descr.split("\n"):
                if box:
                    tmpLine = wrapper.fill(line)
                    for singleLine in tmpLine.split("\n"):
                        singleLine = singleLine.ljust(
                                self.details.get('width'), ' ')
                        new_descr += singleLine[:len(indent)] + \
                            self.printer.art['vrt'] + \
                            singleLine[(len(indent) + 1):
                                       (self.details.get('width') - 1)] + \
                            self.printer.art['vrt'] + '\n'
                else:
                    new_descr += wrapper.fill(line) + "\n"
            return new_descr.rstrip()

        indent = 10 * ' '
        detailsIndent = 19 * ' '

        if self.options['military']:
            timeFormat = '%-5s'
            tmpTimeStr = event['s'].strftime("%H:%M")
        else:
            timeFormat = '%-7s'
            tmpTimeStr = \
                event['s'].strftime("%I:%M").lstrip('0').rjust(5) + \
                event['s'].strftime('%p').lower()

        if not prefix:
            prefix = indent

        self.printer.msg(prefix, self.options['color_date'])

        happeningNow = event['s'] <= self.now <= event['e']
        allDay = self._isallday(event)
        if self.options['override_color'] and event.get('colorId'):
            if happeningNow and not allDay:
                eventColor = self.options['color_now_marker']
            else:
                eventColor = self._calendar_color(
                    event, override_color=True)
        else:
            eventColor = self.options['color_now_marker'] \
                if happeningNow and not allDay \
                else self._calendar_color(event)

        if allDay:
            fmt = '  ' + timeFormat + '  %s\n'
            self.printer.msg(
                    fmt % ('', self._valid_title(event).strip()),
                    eventColor)
        else:
            fmt = '  ' + timeFormat + '  %s\n'
            self.printer.msg(
                    fmt % (
                        tmpTimeStr, self._valid_title(event).strip()),
                    eventColor)

        if self.details.get('calendar'):
            xstr = "%s  Calendar: %s\n" % (
                    detailsIndent, event['gcalcli_cal']['summary'])
            self.printer.msg(xstr, 'default')

        if self.details.get('url') and 'htmlLink' in event:
            hLink = self._shorten_url(event['htmlLink'])
            xstr = "%s  Link: %s\n" % (detailsIndent, hLink)
            self.printer.msg(xstr, 'default')

        if self.details.get('url') and 'hangoutLink' in event:
            hLink = self._shorten_url(event['hangoutLink'])
            xstr = "%s  Hangout Link: %s\n" % (detailsIndent, hLink)
            self.printer.msg(xstr, 'default')

        if self.details.get('location') and \
           'location' in event and \
           event['location'].strip():
            xstr = "%s  Location: %s\n" % (
                detailsIndent,
                event['location'].strip()
            )
            self.printer.msg(xstr, 'default')

        if self.details.get('attendees') and 'attendees' in event:
            xstr = "%s  Attendees:\n" % (detailsIndent)
            self.printer.msg(xstr, 'default')

            if 'self' not in event['organizer']:
                xstr = "%s    %s: <%s>\n" % (
                    detailsIndent,
                    event['organizer'].get('displayName', 'Not Provided')
                                      .strip(),
                    event['organizer'].get('email', 'Not Provided').strip()
                )
                self.printer.msg(xstr, 'default')

            for attendee in event['attendees']:
                if 'self' not in attendee:
                    xstr = "%s    %s: <%s>\n" % (
                        detailsIndent,
                        attendee.get('displayName', 'Not Provided').strip(),
                        attendee.get('email', 'Not Provided').strip()
                    )
                    self.printer.msg(xstr, 'default')

        if self.details.get('attachments') and 'attachments' in event:
            xstr = "%s  Attachments:\n" % (detailsIndent)
            self.printer.msg(xstr, 'default')

            for attendee in event['attachments']:
                xstr = "%s    %s\n%s    -> %s\n" % (
                    detailsIndent,
                    attendee.get('title', 'Not Provided').strip(),
                    detailsIndent,
                    attendee.get('fileUrl', 'Not Provided').strip()
                )
                self.printer.msg(xstr, 'default')

        if self.details.get('length'):
            diffDateTime = (event['e'] - event['s'])
            xstr = "%s  Length: %s\n" % (detailsIndent, diffDateTime)
            self.printer.msg(xstr, 'default')

        if self.details.get('reminders') and 'reminders' in event:
            if event['reminders']['useDefault'] is True:
                xstr = "%s  Reminder: (default)\n" % (detailsIndent)
                self.printer.msg(xstr, 'default')
            elif 'overrides' in event['reminders']:
                for rem in event['reminders']['overrides']:
                    xstr = "%s  Reminder: %s %d minutes\n" % \
                           (detailsIndent, rem['method'], rem['minutes'])
                    self.printer.msg(xstr, 'default')

        if self.details.get('email') and \
           'email' in event['creator'] and \
           event['creator']['email'].strip():
            xstr = "%s  Email: %s\n" % (
                detailsIndent,
                event['creator']['email'].strip()
            )
            self.printer.msg(xstr, 'default')

        if self.details.get('description') and \
           'description' in event and \
           event['description'].strip():
            descrIndent = detailsIndent + '  '
            box = True  # leave old non-box code for option later
            if box:
                topMarker = (descrIndent +
                             self.printer.art['ulc'] +
                             (self.printer.art['hrz'] *
                              ((self.details.get('width') - len(descrIndent)) -
                               2)) +
                             self.printer.art['urc'])
                botMarker = (descrIndent +
                             self.printer.art['llc'] +
                             (self.printer.art['hrz'] *
                              ((self.details.get('width') - len(descrIndent)) -
                               2)) +
                             self.printer.art['lrc'])
                xstr = "%s  Description:\n%s\n%s\n%s\n" % (
                    detailsIndent,
                    topMarker,
                    _formatDescr(event['description'].strip(),
                                 descrIndent, box),
                    botMarker
                )
            else:
                marker = descrIndent + '-' * \
                    (self.details.get('width') - len(descrIndent))
                xstr = "%s  Description:\n%s\n%s\n%s\n" % (
                    detailsIndent,
                    marker,
                    _formatDescr(event['description'].strip(),
                                 descrIndent, box),
                    marker
                )
            self.printer.msg(xstr, 'default')

    def _delete_event(self, event):

        if self.expert:
            self._retry_with_backoff(
                self._cal_service().events().
                delete(calendarId=event['gcalcli_cal']['id'],
                       eventId=event['id']))
            self.printer.msg('Deleted!\n', 'red')
            return

        self.printer.msg('Delete? [N]o [y]es [q]uit: ', 'magenta')
        val = input()

        if not val or val.lower() == 'n':
            return

        elif val.lower() == 'y':
            self._retry_with_backoff(
                self._cal_service().events().
                delete(calendarId=event['gcalcli_cal']['id'],
                       eventId=event['id']))
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
                    'len[g]th [r]eminder [c]olor [d]escr: ', 'magenta')
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
                    self._cal_service().events().
                    patch(calendarId=event['gcalcli_cal']['id'],
                          eventId=event['id'],
                          body=mod_event))
                self.printer.msg("Saved!\n", 'red')
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
                                val, length, all_day)
                    except ValueError as exc:
                        self.printer.err_msg(str(exc))
                        sys.exit(1)
                    event = self._SetEventStartEnd(new_start, new_end, event)

            elif val.lower() == 'g':
                val = get_input(
                    self.printer, 'Length (mins): ', STR_TO_INT)
                if val:
                    all_day = self.options.get('allday')
                try:
                    new_start, new_end = utils.get_times_from_duration(
                            event['start']['dateTime'], val,
                            all_day)
                    event = self._SetEventStartEnd(new_start, new_end, event)
                except ValueError as exc:
                    self.printer.err_msg(str(exc))

            elif val.lower() == 'r':
                rem = []
                while True:
                    r = get_input(
                        self.printer, "Enter a valid reminder or '.' to"
                                      "end: ", REMINDER)
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
                    event, event['s'].strftime('\n%Y-%m-%d'))

    def _iterate_events(
            self, start_datetime, event_list, year_date=False, work=None):

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

        eventList = []

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

                eventList.append(event)

            pageToken = events.get('nextPageToken')
            if pageToken:
                events = self._retry_with_backoff(
                    self._cal_service().events().
                    list(calendarId=cal['id'], pageToken=pageToken))
            else:
                break

        return eventList

    def _search_for_events(self, start, end, search_text):

        event_list = []
        for cal in self.cals:
            work = self._cal_service().events().\
                list(calendarId=cal['id'],
                     timeMin=start.isoformat() if start else None,
                     timeMax=end.isoformat() if end else None,
                     q=search_text if search_text else None,
                     singleEvents=True)
            events = self._retry_with_backoff(work)
            event_list.extend(self._GetAllEvents(cal, events, end))

        event_list.sort(key=lambda x: x['s'])

        return event_list

    def _DeclinedEvent(self, event):
        if 'attendees' in event:
            attendee = [a for a in event['attendees']
                        if a['email'] == event['gcalcli_cal']['id']][0]
            if attendee and attendee['responseStatus'] == 'declined':
                return True
        return False

    def ListAllCalendars(self):
        accessLen = 0

        for cal in self.allCals:
            length = len(cal['accessRole'])
            if length > accessLen:
                accessLen = length

        if accessLen < len('Access'):
            accessLen = len('Access')

        format = ' %0' + str(accessLen) + 's  %s\n'

        self.printer.msg(
                format % ('Access', 'Title'), self.options['color_title'])
        self.printer.msg(
                format % ('------', '-----'), self.options['color_title'])

        for cal in self.allCals:
            self.printer.msg(
                    format % (cal['accessRole'], cal['summary']),
                    self._calendar_color(cal))

    def _display_queried_events(
            self, start, end, search=None, year_date=False):
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

    def AgendaQuery(self, start=None, end=None):
        if not start:
            start = self.now.replace(hour=0, minute=0, second=0, microsecond=0)

        if not end:
            end = (start + timedelta(days=self.agenda_length))

        return self._display_queried_events(start, end)

    def CalQuery(self, cmd, startText='', count=1):
        if not startText:
            # convert now to midnight this morning and use for default
            start = self.now.replace(hour=0,
                                     minute=0,
                                     second=0,
                                     microsecond=0)
        else:
            try:
                start = utils.get_time_from_str(startText)
                start = start.replace(hour=0, minute=0, second=0,
                                      microsecond=0)
            except Exception:
                self.printer.err_msg(
                        'Error: failed to parse start time\n')
                return

        # convert start date to the beginning of the week or month
        if cmd == 'calw':
            dayNum = self._cal_monday(int(start.strftime("%w")))
            start = (start - timedelta(days=dayNum))
            end = (start + timedelta(days=(count * 7)))
        else:  # cmd == 'calm':
            start = (start - timedelta(days=(start.day - 1)))
            endMonth = (start.month + 1)
            endYear = start.year
            if endMonth == 13:
                endMonth = 1
                endYear += 1
            end = start.replace(month=endMonth, year=endYear)
            daysInMonth = (end - start).days
            offsetDays = int(start.strftime('%w'))
            if self.options['cal_monday']:
                offsetDays -= 1
                if offsetDays < 0:
                    offsetDays = 6
            totalDays = (daysInMonth + offsetDays)
            count = int(totalDays / 7)
            if totalDays % 7:
                count += 1

        eventList = self._search_for_events(start, end, None)

        self._GraphEvents(cmd, start, count, eventList)

    def QuickAddEvent(self, event_text, reminders=None):
        """Wrapper around Google Calendar API's quickAdd"""
        if not event_text:
            raise GcalcliError('event_text is required for a quickAdd')

        if len(self.cals) != 1:
            # TODO: get a better name for this exception class
            # and use it elsewhere
            raise GcalcliError('You must only specify a single calendar\n')

        new_event = self._retry_with_backoff(
            self._cal_service().events().quickAdd(
                calendarId=self.cals[0]['id'], text=event_text))

        if reminders or not self.options['default_reminders']:
            rem = {}
            rem['reminders'] = {'useDefault': False,
                                'overrides': []}
            for r in reminders:
                n, m = utils.parse_reminder(r)
                rem['reminders']['overrides'].append({'minutes': n,
                                                      'method': m})

            new_event = self._retry_with_backoff(
                self._cal_service().events().
                patch(calendarId=self.cals[0]['id'],
                      eventId=new_event['id'],
                      body=rem))

        if self.details.get('url'):
            hlink = self._shorten_url(new_event['htmlLink'])
            self.printer.msg('New event added: %s\n' % hlink, 'green')

        return new_event

    def AddEvent(
            self, title, where, start, end, descr, who, reminders, color):

        if len(self.cals) != 1:
            # TODO: get a better name for this exception class
            # and use it elsewhere
            raise GcalcliError('You must only specify a single calendar\n')

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
        events = self._cal_service().events()
        request = events.insert(calendarId=self.cals[0]['id'], body=event)
        new_event = self._retry_with_backoff(request)

        if self.details.get('url'):
            hlink = self._shorten_url(new_event['htmlLink'])
            self.printer.msg('New event added: %s\n' % hlink, 'green')

        return new_event

    def ModifyEvents(
            self, work, search_text, start=None, end=None, expert=False):
        if not search_text:
            raise GcalcliError('The empty string would get *ALL* events')

        event_list = self._search_for_events(start, end, search_text)
        self.expert = expert
        return self._iterate_events(
                self.now, event_list, year_date=True, work=work)

    def Remind(self, minutes, command, use_reminders=False):
        """Check for events between now and now+minutes.  If use_reminders then
           only remind if now >= event['start'] - reminder"""

        # perform a date query for now + minutes + slip
        start = self.now
        end = (start + timedelta(minutes=(minutes + 5)))

        eventList = self._search_for_events(start, end, None)

        message = ''

        for event in eventList:

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
                print("+----------------+")
                print("| Calendar Event |")
                print("+----------------+")

            if hasattr(ve, 'summary'):
                if verbose:
                    print("Event........%s" % ve.summary.value)
                event['summary'] = ve.summary.value

            if hasattr(ve, 'location'):
                if verbose:
                    print("Location.....%s" % ve.location.value)
                event['location'] = ve.location.value

            if not hasattr(ve, 'dtstart') or not hasattr(ve, 'dtend'):
                self.printer.err_msg(
                        'Error: event does not have a dtstart and dtend!\n')
                return None

            if verbose:
                if ve.dtstart.value:
                    print("Start........%s" % ve.dtstart.value.isoformat())
                if ve.dtend.value:
                    print("End..........%s" % ve.dtend.value.isoformat())
                if ve.dtstart.value:
                    print("Local Start..%s" % self._localize_datetime(
                        ve.dtstart.value))
                if ve.dtend.value:
                    print("Local End....%s" % self._localize_datetime(
                        ve.dtend.value))

            if hasattr(ve, 'rrule'):
                if verbose:
                    print("Recurrence...%s" % ve.rrule.value)

                event['recurrence'] = ["RRULE:" + ve.rrule.value]

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
                    print("Description:\n%s" % descr)
                event['description'] = descr

            if hasattr(ve, 'organizer'):
                if ve.organizer.value.startswith("MAILTO:"):
                    email = ve.organizer.value[7:]
                else:
                    email = ve.organizer.value
                if verbose:
                    print("organizer:\n %s" % email)
                event['organizer'] = {'displayName': ve.organizer.name,
                                      'email': email}

            if hasattr(ve, 'attendee_list'):
                if verbose:
                    print("attendees:")
                event['attendees'] = []
                for attendee in ve.attendee_list:
                    if attendee.value.upper().startswith("MAILTO:"):
                        email = attendee.value[7:]
                    else:
                        email = attendee.value
                    if verbose:
                        print(" %s" % email)

                    event['attendees'].append({'displayName': attendee.name,
                                               'email': email})

            return event

        try:
            import vobject
        except ImportError:
            self.printer.err_msg(
                    'Python vobject module not installed!\n')
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
                    newEvent = self._retry_with_backoff(
                        self._cal_service().events().
                        insert(calendarId=self.cals[0]['id'],
                               body=event))
                    hlink = self._shorten_url(newEvent.get('htmlLink'))
                    self.printer.msg(
                            'New event added: %s\n' % hlink, 'green')
                    continue

                self.printer.msg('\n[S]kip [i]mport [q]uit: ', 'magenta')
                val = input()
                if not val or val.lower() == 's':
                    continue
                if val.lower() == 'i':
                    newEvent = self._retry_with_backoff(
                        self._cal_service().events().
                        insert(calendarId=self.cals[0]['id'],
                               body=event))
                    hlink = self._shorten_url(newEvent.get('htmlLink'))
                    self.printer.msg('New event added: %s\n' % hlink, 'green')
                elif val.lower() == 'q':
                    sys.exit(0)
                else:
                    self.printer.err_msg('Error: invalid input\n')
                    sys.exit(1)
        # TODO: return the number of events added
        return True


def parse_cal_names(cal_names):
    cal_colors = {}
    for name in cal_names:
        cal_color = 'default'
        parts = name.split("#")
        parts_count = len(parts)
        if parts_count >= 1:
            cal_name = parts[0]

        if len(parts) == 2:
            cal_color = valid_color_name(parts[1])

        if len(parts) > 2:
            raise ValueError('Cannot parse calendar name: "%s"' % name)

        cal_colors[cal_name] = cal_color
    return [CalName(name=k, color=cal_colors[k]) for k in cal_colors.keys()]


def main():
    parser = get_argument_parser()
    try:
        argv = sys.argv[1:]
        gcalclirc = os.path.expanduser('~/.gcalclirc')
        if os.path.exists(gcalclirc):
            # We want .gcalclirc to be sourced before any other --flagfile
            # params since we may be told to use a specific config folder, we
            # need to store generated argv in temp variable
            tmpArgv = ["@%s" % gcalclirc, ] + argv
        else:
            tmpArgv = argv
        # TODO: In 4.1 change this to just parse_args
        (FLAGS, junk) = parser.parse_known_args(tmpArgv)
    except Exception as e:
        sys.stderr.write(str(e))
        parser.print_usage()
        sys.exit(1)

    if FLAGS.configFolder:
        if not os.path.exists(os.path.expanduser(FLAGS.configFolder)):
            os.makedirs(os.path.expanduser(FLAGS.configFolder))
        if os.path.exists(os.path.expanduser("%s/gcalclirc" %
                                             FLAGS.configFolder)):
            if not FLAGS.includeRc:
                tmpArgv = ["@%s/gcalclirc" % FLAGS.configFolder, ] + argv
            else:
                tmpArgv = ["@%s/gcalclirc" % FLAGS.configFolder, ] + tmpArgv

        # TODO: In 4.1 change this to just parse_args
        (FLAGS, junk) = parser.parse_known_args(tmpArgv)

    printer = Printer(
            conky=FLAGS.conky, use_color=FLAGS.color, art_style=FLAGS.lineart)

    if junk:
        prog_level_opts_msg = (
            "\nPlease note that the following options MUST be given before the"
            " subcommand ('list', 'edit', etc):\n"
            "    --client_id\n"
            "    --client_secret\n"
            "    --configFolder\n"
            "    --noincluderc\n"
            "    --calendar\n"
            "    --defaultCalendar\n"
            "    --locale\n"
            "    --refresh\n"
            "    --nocache\n"
            "    --conky\n"
            "    --nocolor\n"
            "    --linart\n"
        )
        printer.err_msg(
            "WARNING: The following options are either no longer valid "
            "globally or just plain invalid:\n  %s\n" % "\n  ".join(junk))
        printer.msg(prog_level_opts_msg, "yellow")
        printer.msg("(continuing to process your request using defaults...)\n")

    if FLAGS.locale:
        try:
            utils.set_locale(FLAGS.locale)
        except ValueError as exc:
            printer.err_msg(str(exc))

    if len(FLAGS.calendar) == 0:
        FLAGS.calendar = FLAGS.defaultCalendar

    cal_names = parse_cal_names(FLAGS.calendar)
    gcal = GoogleCalendarInterface(
            cal_names=cal_names, printer=printer, **vars(FLAGS))

    try:
        if FLAGS.command == 'list':
            gcal.ListAllCalendars()

        elif FLAGS.command == 'agenda':
            gcal.AgendaQuery(start=FLAGS.start, end=FLAGS.end)

        elif FLAGS.command == 'calw':
            gcal.CalQuery(
                    FLAGS.command, count=FLAGS.weeks, startText=FLAGS.start)

        elif FLAGS.command == 'calm':
            gcal.CalQuery(FLAGS.command, startText=FLAGS.start)

        elif FLAGS.command == 'quick':
            if not FLAGS.text:
                printer.err_msg('Error: invalid event text\n')
                sys.exit(1)

            # allow unicode strings for input
            gcal.QuickAddEvent(_u(FLAGS.text), reminders=FLAGS.reminders)

        elif FLAGS.command == 'add':
            if FLAGS.prompt:
                if FLAGS.title is None:
                    FLAGS.title = get_input(printer, 'Title: ', STR_NOT_EMPTY)
                if FLAGS.where is None:
                    FLAGS.where = get_input(
                        printer, 'Location: ', STR_ALLOW_EMPTY)
                if FLAGS.when is None:
                    FLAGS.when = get_input(printer, 'When: ', PARSABLE_DATE)
                if FLAGS.duration is None:
                    if FLAGS.allday:
                        prompt = 'Duration (days): '
                    else:
                        prompt = 'Duration (minutes): '
                    FLAGS.duration = get_input(printer, prompt, STR_TO_INT)
                if FLAGS.description is None:
                    FLAGS.description = get_input(
                        printer, 'Description: ', STR_ALLOW_EMPTY)
                if FLAGS.event_color is None:
                    FLAGS.event_color = get_input(
                        printer, "Color: ", VALID_COLORS)
                if not FLAGS.reminders:
                    while True:
                        r = get_input(printer, "Enter a valid reminder or "
                                               "'.' to end: ", REMINDER)

                        if r == '.':
                            break
                        n, m = utils.parse_reminder(str(r))
                        FLAGS.reminders.append(str(n) + ' ' + m)

            # calculate "when" time:
            try:
                estart, eend = utils.get_times_from_duration(
                        FLAGS.when, FLAGS.duration, FLAGS.allday)
            except ValueError as exc:
                printer.err_msg(str(exc))
                # Since we actually need a valid start and end time in order to
                # add the event, we cannot proceed.
                raise

            gcal.AddEvent(FLAGS.title, FLAGS.where, estart, eend,
                          FLAGS.description, FLAGS.who,
                          FLAGS.reminders, FLAGS.event_color)

        elif FLAGS.command == 'search':
            gcal.TextQuery(FLAGS.text[0], start=FLAGS.start, end=FLAGS.end)

        elif FLAGS.command == 'delete':
            gcal.ModifyEvents(
                    gcal._delete_event, FLAGS.text[0],
                    start=FLAGS.start, end=FLAGS.end, expert=FLAGS.iamaexpert)

        elif FLAGS.command == 'edit':
            gcal.ModifyEvents(
                    gcal._edit_event, FLAGS.text[0], start=FLAGS.start,
                    end=FLAGS.end)

        elif FLAGS.command == 'remind':
            gcal.Remind(
                    FLAGS.minutes, FLAGS.cmd,
                    use_reminders=FLAGS.use_reminders)

        elif FLAGS.command == 'import':
            gcal.ImportICS(
                    FLAGS.verbose, FLAGS.dump, FLAGS.reminders, FLAGS.file)

    except GcalcliError as exc:
        printer.err_msg(str(exc))
        sys.exit(1)


def SIGINT_handler(signum, frame):
    sys.stderr.write('Signal caught, bye!\n')
    sys.exit(1)


signal.signal(signal.SIGINT, SIGINT_handler)


if __name__ == '__main__':
    main()
