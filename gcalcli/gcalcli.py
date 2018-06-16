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
# Home: https://github.com/insanum/gcalcli                                  #
#                                                                           #
# Requirements:                                                             #
#  - Python 2                                                               #
#        http://www.python.org                                              #
#  - Google APIs Client Library for Python 2                                #
#        https://developers.google.com/api-client-library/python            #
#  - dateutil Python 2 module                                               #
#        http://www.labix.org/python-dateutil                               #
#                                                                           #
# Optional:                                                                 #
#  - vobject Python module (needed for importing ics/vcal files)            #
#        http://vobject.skyhouseconsulting.com                              #
#  - parsedatetime Python module (needed for fuzzy date parsing)            #
#        https://github.com/bear/parsedatetime                              #
#                                                                           #
# Everything you need to know (Google API Calendar v3): http://goo.gl/HfTGQ #
#                                                                           #
#############################################################################
from __future__ import print_function

__program__ = 'gcalcli'
__version__ = 'v4.0.0a4'
__author__ = 'Eric Davis, Brian Hartvigsen'
__API_CLIENT_ID__ = '232867676714.apps.googleusercontent.com'
__API_CLIENT_SECRET__ = '3tZSxItw6_VnZMezQwC8lUqy'

# Package local imports
from color_printer import ColorPrinter, valid_color_name

# These are standard libraries and should never fail
import sys
import os
import re
import shlex
import time
import calendar
import locale
import textwrap
import signal
import json
import random
import argparse
from datetime import datetime, timedelta, date
from unicodedata import east_asian_width
from io import BytesIO

# Required 3rd party libraries
try:
    from dateutil.tz import tzlocal
    from dateutil.parser import parse
    import httplib2
    import six
    from six.moves import range, zip, map, cPickle as pickle
    from apiclient.discovery import build
    from apiclient.errors import HttpError
    from oauth2client.file import Storage
    from oauth2client.client import OAuth2WebServerFlow
    from oauth2client import tools
except ImportError as e:
    print("ERROR: Missing module - %s" % e.args[0])
    sys.exit(1)

# If they have parsedatetime, we'll use it for fuzzy datetime comparison.  If
# not, we just return a fake failure every time and use only dateutil.
try:
    from parsedatetime import parsedatetime
except ImportError:
    class parsedatetime:
        class Calendar:
            def parse(self, string):
                return ([], 0)

locale.setlocale(locale.LC_ALL, "")


def _u(string):
    encoding = locale.getlocale()[1] or \
            locale.getpreferredencoding(False) or "UTF-8"
    if issubclass(type(string), six.text_type):
        return string
    if not issubclass(type(string), six.string_types):
        if six.PY3:
            if isinstance(string, bytes):
                return six.text_type(string, encoding, "replace")
            else:
                return six.text_type(string)
        elif hasattr(string, '__unicode__'):
            return six.text_type(string)
        else:
            return six.text_type(bytes(string), encoding, "replace")
    else:
        return string.decode(encoding, "replace")




class ART:

    useArt = True
    fancy = ''
    plain = ''

    def __str__(self):
        return self.fancy if self.useArt else self.plain


class ART_HRZ(ART):
    fancy = '\033(0\x71\033(B'
    plain = '-'


class ART_VRT(ART):
    fancy = '\033(0\x78\033(B'
    plain = '|'


class ART_LRC(ART):
    fancy = '\033(0\x6A\033(B'
    plain = '+'


class ART_URC(ART):
    fancy = '\033(0\x6B\033(B'
    plain = '+'


class ART_ULC(ART):
    fancy = '\033(0\x6C\033(B'
    plain = '+'


class ART_LLC(ART):
    fancy = '\033(0\x6D\033(B'
    plain = '+'


class ART_CRS(ART):
    fancy = '\033(0\x6E\033(B'
    plain = '+'


class ART_LTE(ART):
    fancy = '\033(0\x74\033(B'
    plain = '+'


class ART_RTE(ART):
    fancy = '\033(0\x75\033(B'
    plain = '+'


class ART_BTE(ART):
    fancy = '\033(0\x76\033(B'
    plain = '+'


class ART_UTE(ART):
    fancy = '\033(0\x77\033(B'
    plain = '+'




def dprint(obj):
    try:
        from pprint import pprint
        pprint(obj)
    except ImportError:
        print(obj)


class DateTimeParser:
    def __init__(self):
        self.pdtCalendar = parsedatetime.Calendar()

    def fromString(self, eWhen):
        defaultDateTime = datetime.now(tzlocal()).replace(hour=0,
                                                          minute=0,
                                                          second=0,
                                                          microsecond=0)

        try:
            eTimeStart = parse(eWhen, default=defaultDateTime)
        except Exception:
            struct, result = self.pdtCalendar.parse(eWhen)
            if not result:
                raise ValueError("Date and time is invalid")
            eTimeStart = datetime.fromtimestamp(time.mktime(struct), tzlocal())

        return eTimeStart


def DaysSinceEpoch(dt):
    # Because I hate magic numbers
    __DAYS_IN_SECONDS__ = 24 * 60 * 60
    return calendar.timegm(dt.timetuple()) / __DAYS_IN_SECONDS__


def GetTimeFromStr(eWhen, eDuration=0, allday=False):
    dtp = DateTimeParser()

    try:
        eTimeStart = dtp.fromString(eWhen)
    except Exception:
        raise ValueError('Date and time is invalid!\n')

    if allday:
        try:
            eTimeStop = eTimeStart + timedelta(days=float(eDuration))
        except Exception:
            raise ValueError('Duration time (days) is invalid\n')

        sTimeStart = eTimeStart.date().isoformat()
        sTimeStop = eTimeStop.date().isoformat()

    else:
        try:
            eTimeStop = eTimeStart + timedelta(minutes=float(eDuration))
        except Exception:
            raise ValueError('Duration time (minutes) is invalid\n')

        sTimeStart = eTimeStart.isoformat()
        sTimeStop = eTimeStop.isoformat()

    return sTimeStart, sTimeStop


def ParseReminder(rem):
    matchObj = re.match(r'^(\d+)([wdhm]?)(?:\s+(popup|email|sms))?$', rem)
    if not matchObj:
        # Allow argparse to generate a message when parsing options
        return None
    n = int(matchObj.group(1))
    t = matchObj.group(2)
    m = matchObj.group(3)
    if t == 'w':
        n = n * 7 * 24 * 60
    elif t == 'd':
        n = n * 24 * 60
    elif t == 'h':
        n = n * 60

    if not m:
        m = 'popup'

    return n, m


DETAILS = ['all', 'calendar', 'location', 'length', 'reminders', 'description',
           'longurl', 'shorturl', 'url', 'attendees', 'email', 'attachments']


class GoogleCalendarInterface:

    cache = {}
    allCals = []
    allEvents = []
    cals = []
    now = datetime.now(tzlocal())
    agendaLength = 5
    maxRetries = 5
    authHttp = None
    calService = None
    urlService = None
    command = 'notify-send -u critical -a gcalcli %s'
    dateParser = DateTimeParser()

    ACCESS_OWNER = 'owner'
    ACCESS_WRITER = 'writer'
    ACCESS_READER = 'reader'
    ACCESS_FREEBUSY = 'freeBusyReader'

    UNIWIDTH = {'W': 2, 'F': 2, 'N': 1, 'Na': 1, 'H': 1, 'A': 1}

    def __init__(
            self, calNames=[], calNameColors=[], color_printer=ColorPrinter(),
            **options):
        self.color_printer = color_printer
        self.options = options

        self.details = {}
        chosen_details = options.get('details', [])
        for choice in DETAILS:
            self.details[choice] = \
                    'all' in chosen_details or choice in chosen_details
        self.details['url'] = ('short' if 'shorturl' in chosen_details else
                               'long' if 'longurl' in chosen_details else
                               None)
        # stored as detail, but provided as option
        self.details['width'] = options.get('width', 80)
        self._GetCached()

        if len(calNames):
            # Changing the order of this and the `cal in self.allCals` loop
            # is necessary for the matching to actually be sane (ie match
            # supplied name to cached vs matching cache against supplied names)
            for i in range(len(calNames)):
                matches = []
                for cal in self.allCals:
                    # For exact match, we should match only 1 entry and accept
                    # the first entry.  Should honor access role order since
                    # it happens after _GetCached()
                    if calNames[i] == cal['summary']:
                        # This makes sure that if we have any regex matches
                        # that we toss them out in favor of the specific match
                        matches = [cal]
                        cal['colorSpec'] = calNameColors[i]
                        break
                    # Otherwise, if the calendar matches as a regex, append
                    # it to the list of potential matches
                    elif re.search(calNames[i], cal['summary'], flags=re.I):
                        matches.append(cal)
                        cal['colorSpec'] = calNameColors[i]
                # Add relevant matches to the list of calendars we want to
                # operate against
                self.cals += matches
        else:
            self.cals = self.allCals

    @staticmethod
    def _LocalizeDateTime(dt):
        if not hasattr(dt, 'tzinfo'):
            return dt
        if dt.tzinfo is None:
            return dt.replace(tzinfo=tzlocal())
        else:
            return dt.astimezone(tzlocal())

    def _RetryWithBackoff(self, method):
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

    def _GoogleAuth(self):
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
                    self.options)

            self.authHttp = credentials.authorize(httplib2.Http())

        return self.authHttp

    def _CalService(self):
        if not self.calService:
            self.calService = \
                build(serviceName='calendar',
                      version='v3',
                      http=self._GoogleAuth())

        return self.calService

    def _UrlService(self):
        if not self.urlService:
            self._GoogleAuth()
            self.urlService = \
                build(serviceName='urlshortener',
                      version='v1',
                      http=self._GoogleAuth())

        return self.urlService

    def _GetCached(self):
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

        calList = self._RetryWithBackoff(
            self._CalService().calendarList().list())

        while True:
            for cal in calList['items']:
                self.allCals.append(cal)
            pageToken = calList.get('nextPageToken')
            if pageToken:
                calList = self._RetryWithBackoff(
                    self._CalService().calendarList().list(
                        pageToken=pageToken))
            else:
                break

        self.allCals.sort(key=lambda x: x['accessRole'])

        if self.options['use_cache']:
            self.cache['allCals'] = self.allCals
            with open(cacheFile, 'wb') as _cache_:
                pickle.dump(self.cache, _cache_)

    def _ShortenURL(self, url):
        if self.details['url'] != "short":
            return url
        # Note that when authenticated to a google account different shortUrls
        # can be returned for the same longUrl. See: http://goo.gl/Ya0A9
        shortUrl = self._RetryWithBackoff(
            self._UrlService().url().insert(body={'longUrl': url}))
        return shortUrl['id']

    def _CalendarColor(self, cal):

        if cal is None:
            return 'default'
        elif 'colorSpec' in cal and cal['colorSpec'] is not None:
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

    def _ValidTitle(self, event):
        if 'summary' in event and event['summary'].strip():
            return event['summary']
        else:
            return "(No title)"

    def _IsAllDay(self, event):
        return event['s'].hour == 0 and event['s'].minute == 0 and \
            event['e'].hour == 0 and event['e'].minute == 0

    def _GetWeekEventStrings(self, cmd, curMonth,
                             startDateTime, endDateTime, eventList):

        weekEventStrings = ['', '', '', '', '', '', '']

        nowMarkerPrinted = False
        if self.now < startDateTime or self.now > endDateTime:
            # now isn't in this week
            nowMarkerPrinted = True

        for event in eventList:
            if cmd == 'calm' and curMonth != event['s'].strftime("%b"):
                continue

            dayNum = int(event['s'].strftime("%w"))
            if self.options['cal_monday']:
                dayNum -= 1
                if dayNum < 0:
                    dayNum = 6

            allDay = self._IsAllDay(event)

            # NOTE(slawqo): in allDay events end date is always set as day+1
            # and hour 0:00 so to not display it one day more, it's necessary
            # to lower it by one day:
            if allDay:
                eventEndDate = event['e'] - timedelta(days=1)
            else:
                eventEndDate = event['e']

            # NOTE(slawqo): it's necessary to process events which starts in
            # current period of time but for all day events also to process
            # events which was started before current period of time and are
            # still continue in current period of time
            if ((event['s'] >= startDateTime and event['s'] < endDateTime) or
                (allDay and event['s'] < startDateTime and
                    eventEndDate >= startDateTime)):

                forceEventColorAsMarker = False

                if not nowMarkerPrinted:
                    if (DaysSinceEpoch(self.now) <
                            DaysSinceEpoch(event['s'])):
                        nowMarkerPrinted = True
                        weekEventStrings[dayNum - 1] += \
                            ("\n" +
                             self.color_printer.get_colorcode(self.options['color_now_marker']) +
                             (self.options['cal_width'] * '-'))
                    elif self.now <= event['s']:
                        # add a line marker before next event
                        nowMarkerPrinted = True
                        weekEventStrings[dayNum] += \
                            ("\n" +
                             self.color_printer.get_colorcode(self.options['color_now_marker']) +
                             (self.options['cal_width'] * '-'))
                    # We don't want to recolor all day events, but ignoring
                    # them leads to issues where the "now" marker misprints
                    # into the wrong day.  This resolves the issue by skipping
                    # all day events for specific coloring but not for previous
                    # or next events
                    elif self.now >= event['s'] and \
                            self.now <= eventEndDate and \
                            not allDay:
                        # line marker is during the event (recolor event)
                        nowMarkerPrinted = True
                        forceEventColorAsMarker = True

                if allDay:
                    tmpTimeStr = ''
                elif self.options['military']:
                    tmpTimeStr = event['s'].strftime("%H:%M")
                else:
                    tmpTimeStr = \
                        event['s'].strftime("%I:%M").lstrip('0') + \
                        event['s'].strftime('%p').lower()

                if forceEventColorAsMarker:
                    eventColor = self.options['color_now_marker']
                else:
                    eventColor = self._CalendarColor(event['gcalcli_cal'])

                # NOTE(slawqo): for all day events it's necessary to add event
                # to more than one day in weekEventStrings
                if allDay and event['s'] < eventEndDate:
                    if eventEndDate > endDateTime:
                        endDayNum = 6
                    else:
                        endDayNum = int(eventEndDate.strftime("%w"))
                        if self.options['cal_monday']:
                            endDayNum -= 1
                            if endDayNum < 0:
                                endDayNum = 6
                    if dayNum > endDayNum:
                        dayNum = 0
                    for day in range(dayNum, endDayNum + 1):
                        # newline and empty string are the keys to turn off
                        # coloring
                        weekEventStrings[day] += \
                            "\n" + \
                            _u(self.color_printer.get_colorcode(eventColor)) + \
                            _u(tmpTimeStr.strip()) + \
                            " " + \
                            _u(self._ValidTitle(event).strip())
                else:
                    # newline and empty string are the keys to turn off
                    # coloring
                    weekEventStrings[dayNum] += \
                        "\n" + \
                        _u(self.color_printer.get_colorcode(eventColor)) + \
                        _u(tmpTimeStr.strip()) + \
                        " " + \
                        _u(self._ValidTitle(event).strip())

        return weekEventStrings

    def _PrintLen(self, string):
        # We need to treat everything as unicode for this to actually give
        # us the info we want.  Date string were coming in as `str` type
        # so we convert them to unicode and then check their size. Fixes
        # the output issues we were seeing around non-US locale strings
        printLen = 0
        for tmpChar in _u(string):
            printLen += self.UNIWIDTH[east_asian_width(tmpChar)]
        return printLen

    # return print length before cut, cut index, and force cut flag
    def _NextCut(self, string, curPrintLen):
        idx = 0
        printLen = 0
        for tmpChar in _u(string):
            printTmpChar = self.UNIWIDTH[east_asian_width(tmpChar)]
            if (curPrintLen + printLen + printTmpChar) > \
                    self.options['cal_width']:
                return (printLen, idx, True)
            if tmpChar in (' ', '\n'):
                return (printLen, idx, False)
            idx += 1
            printLen += printTmpChar
        return (printLen, -1, False)

    def _GetCutIndex(self, eventString):

        printLen = self._PrintLen(eventString)

        if printLen <= self.options['cal_width']:
            if '\n' in eventString:
                idx = eventString.find('\n')
                printLen = self._PrintLen(eventString[:idx])
            else:
                idx = len(eventString)

            # DebugPrint("------ printLen=%d (end of string)\n" % idx)
            return (printLen, idx)

        cutWidth, cut, forceCut = self._NextCut(eventString, 0)

        if forceCut:
            return (cutWidth, cut)

        while cutWidth < self.options['cal_width']:
            while cut < self.options['cal_width'] and \
                    cut < printLen and \
                    eventString[cut] == ' ':
                cutWidth += 1
                cut += 1

            nextCutWidth, nextCut, forceCut = \
                self._NextCut(eventString[cut:], cutWidth)

            if forceCut:
                break

            cutWidth += nextCutWidth
            cut += nextCut

            if eventString[cut] == '\n':
                break

        return (cutWidth, cut)

    def _GraphEvents(self, cmd, startDateTime, count, eventList):
        # ignore started events (i.e. events that start previous day and end
        # start day)

        # Build up a buffer of bytes to flush
        buf = BytesIO()


        while (len(eventList) and eventList[0]['s'] < startDateTime):
            eventList = eventList[1:]

        dayWidthLine = (self.options['cal_width'] * str(ART_HRZ()))

        dayNums = range(7) if self.options['cal_weekend'] else range(1, 6)
        days = len(dayNums)

        topWeekDivider = (str(ART_ULC()) + dayWidthLine +
                          ((days - 1) * (str(ART_UTE()) + dayWidthLine)) +
                          str(ART_URC()))

        midWeekDivider = (str(ART_LTE()) + dayWidthLine +
                          ((days - 1) * (str(ART_CRS()) + dayWidthLine)) +
                          str(ART_RTE()))

        botWeekDivider = (str(ART_LLC()) + dayWidthLine +
                          ((days - 1) * (str(ART_BTE()) + dayWidthLine)) +
                          str(ART_LRC()))

        empty = self.options['cal_width'] * ' '

        # Get the localized day names... January 1, 2001 was a Monday
        dayNames = [date(2001, 1, i + 1).strftime('%A') for i in range(7)]
        dayNames = dayNames[6:] + dayNames[:6]

        self.color_printer.msg(str(ART_VRT()), self.options['color_border'],
                file=buf)

        for i in dayNums:
            if self.options['cal_monday']:
                if i == 6:
                    dayName = dayNames[0]
                else:
                    dayName = dayNames[i + 1]
            else:
                dayName = dayNames[i]

            dayName += ' ' * (
                    self.options['cal_width'] - self._PrintLen(dayName))

            self.color_printer.msg(dayName, self.options['color_date'],
                    file=buf)
            self.color_printer.msg(str(ART_VRT()),
                    self.options['color_border'], file=buf)

        if cmd == 'calm':
            # top of month
            self.color_printer.msg('\n' + str(ART_ULC()) + dayWidthLine +
                                  ((days - 1) * (str(ART_HRZ()) + dayWidthLine)) +
                                  str(ART_URC()) + '\n',
                                  self.options['color_border'])

            m = startDateTime.strftime('%B %Y')
            mw = (self.options['cal_width'] * days) + (days - 1)
            m += ' ' * (mw - self._PrintLen(m))

            self.color_printer.msg(str(ART_VRT()), self.options['color_border'])
            self.color_printer.msg(m, self.options['color_date'])
            self.color_printer.msg(
                    str(ART_VRT()) + '\n', self.options['color_border'])

            # bottom of month
            self.color_printer.msg(str(ART_LTE()) + dayWidthLine +
                              ((days - 1) * (str(ART_UTE()) + dayWidthLine)) +
                              str(ART_RTE()) + '\n',
                              self.options['color_border'])

        else:  # calw
            # top of week
            self.color_printer.msg('\n' + topWeekDivider + '\n',
                              self.options['color_border'])

        buf.seek(0)
        print(buf.read())
        self.color_printer.msg(midWeekDivider + '\n',
                self.options['color_border'])

        curMonth = startDateTime.strftime("%b")

        # get date range objects for the first week
        if cmd == 'calm':
            dayNum = int(startDateTime.strftime("%w"))
            if self.options['cal_monday']:
                dayNum -= 1
                if dayNum < 0:
                    dayNum = 6
            startDateTime = (startDateTime - timedelta(days=dayNum))
        startWeekDateTime = startDateTime
        endWeekDateTime = (startWeekDateTime + timedelta(days=7))

        for i in range(count):

            # create and print the date line for a week
            for j in dayNums:
                if cmd == 'calw':
                    d = (startWeekDateTime +
                         timedelta(days=j)).strftime("%d %b")
                else:  # (cmd == 'calm'):
                    d = (startWeekDateTime +
                         timedelta(days=j)).strftime("%d")
                    if curMonth != (startWeekDateTime +
                                    timedelta(days=j)).strftime("%b"):
                        d = ''
                tmpDateColor = self.options['color_date']

                if self.now.strftime("%d%b%Y") == \
                   (startWeekDateTime + timedelta(days=j)).strftime("%d%b%Y"):
                    tmpDateColor = self.options['color_now_marker']
                    d += " **"

                d += ' ' * (self.options['cal_width'] - self._PrintLen(d))

                # print dates 
                self.color_printer.msg(str(ART_VRT()), self.options['color_border'])
                self.color_printer.msg(d, tmpDateColor)

            self.color_printer.msg(str(ART_VRT()) + '\n',
                              self.options['color_border'])

            weekColorStrings = ['', '', '', '', '', '', '']
            weekEventStrings = self._GetWeekEventStrings(cmd, curMonth,
                                                         startWeekDateTime,
                                                         endWeekDateTime,
                                                         eventList)

            # get date range objects for the next week
            startWeekDateTime = endWeekDateTime
            endWeekDateTime = (endWeekDateTime + timedelta(days=7))

            while 1:
                done = True
                buf = BytesIO()
                self.color_printer.msg(str(ART_VRT()),
                        self.options['color_border'], file=buf)
                for j in dayNums:
                    if not weekEventStrings[j]:
                        # no events today
                        weekColorStrings[j] = ''
                        self.color_printer.msg(empty + str(ART_VRT()),
                                self.options['color_border'], file=buf)

                        continue

                    # get/skip over a color sequence
                    weekEventStrings[j], weekColorStrings[j] = \
                            self.color_printer.remove_colorcodes(
                                    weekEventStrings[j], weekColorStrings[j])

                    if weekEventStrings[j][0] == '\n':
                        weekColorStrings[j] = ''
                        weekEventStrings[j] = weekEventStrings[j][1:]
                        self.color_printer.msg(
                                empty + str(ART_VRT()),
                                self.options['color_border'], file=buf)
                        done = False
                        continue

                    weekEventStrings[j] = weekEventStrings[j].lstrip()

                    printLen, cut = self._GetCutIndex(weekEventStrings[j])
                    padding = ' ' * (self.options['cal_width'] - printLen)

                    self.color_printer.msg(weekColorStrings[j] +
                                           weekEventStrings[j][:cut] +
                                           padding, 'default', file=buf)

                    weekEventStrings[j] = weekEventStrings[j][cut:]

                    done = False
                    self.color_printer.msg(str(ART_VRT()),
                            self.options['color_border'], file=buf)

                if done:
                    break

                buf.seek(0)
                print(buf.read())

            if i < range(count)[len(range(count)) - 1]:
                self.color_printer.msg(midWeekDivider + '\n', self.options['color_border'])
            else:
                self.color_printer.msg(botWeekDivider + '\n', self.options['color_border'])

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

            if self.details['url']:
                output += "\t%s" % (self._ShortenURL(event['htmlLink'])
                                    if 'htmlLink' in event else '')
                output += "\t%s" % (self._ShortenURL(event['hangoutLink'])
                                    if 'hangoutLink' in event else '')

            output += "\t%s" % _u(self._ValidTitle(event).strip())

            if self.details['location']:
                output += "\t%s" % (_u(event['location'].strip())
                                    if 'location' in event else '')

            if self.details['description']:
                output += "\t%s" % (_u(event['description'].strip())
                                    if 'description' in event else '')

            if self.details['calendar']:
                output += "\t%s" % _u(event['gcalcli_cal']['summary'].strip())

            if self.details['email']:
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
                wrapper.width = (self.details['width'] - 2)
            else:
                wrapper.initial_indent = indent
                wrapper.subsequent_indent = indent
                wrapper.width = self.details['width']
            new_descr = ""
            for line in descr.split("\n"):
                if box:
                    tmpLine = wrapper.fill(line)
                    for singleLine in tmpLine.split("\n"):
                        singleLine = singleLine.ljust(self.details['width'],
                                                      ' ')
                        new_descr += singleLine[:len(indent)] + \
                            str(ART_VRT()) + \
                            singleLine[(len(indent) + 1):
                                       (self.details['width'] - 1)] + \
                            str(ART_VRT()) + '\n'
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

        self.color_printer.msg(prefix, self.options['color_date'])

        happeningNow = event['s'] <= self.now <= event['e']
        allDay = self._IsAllDay(event)
        eventColor = self.options['color_now_marker'] \
            if happeningNow and not allDay \
            else self._CalendarColor(event['gcalcli_cal'])

        if allDay:
            fmt = '  ' + timeFormat + '  %s\n'
            self.color_printer.msg(fmt % ('', _u(self._ValidTitle(event).strip())),
                              eventColor)
        else:
            fmt = '  ' + timeFormat + '  %s\n'
            self.color_printer.msg(fmt % (
                    _u(tmpTimeStr), _u(self._ValidTitle(event).strip())),
                    eventColor)

        if self.details['calendar']:
            xstr = "%s  Calendar: %s\n" % (
                    detailsIndent, event['gcalcli_cal']['summary'])
            self.color_printer.msg(xstr, 'default')

        if self.details['url'] and 'htmlLink' in event:
            hLink = self._ShortenURL(event['htmlLink'])
            xstr = "%s  Link: %s\n" % (detailsIndent, hLink)
            self.color_printer.msg(xstr, 'default')

        if self.details['url'] and 'hangoutLink' in event:
            hLink = self._ShortenURL(event['hangoutLink'])
            xstr = "%s  Hangout Link: %s\n" % (detailsIndent, hLink)
            self.color_printer.msg(xstr, 'default')

        if self.details['location'] and \
           'location' in event and \
           event['location'].strip():
            xstr = "%s  Location: %s\n" % (
                detailsIndent,
                event['location'].strip()
            )
            self.color_printer.msg(xstr, 'default')

        if self.details['attendees'] and 'attendees' in event:
            xstr = "%s  Attendees:\n" % (detailsIndent)
            self.color_printer.msg(xstr, 'default')

            if 'self' not in event['organizer']:
                xstr = "%s    %s: <%s>\n" % (
                    detailsIndent,
                    event['organizer'].get('displayName', 'Not Provided')
                                      .strip(),
                    event['organizer'].get('email', 'Not Provided').strip()
                )
                self.color_printer.msg(xstr, 'default')

            for attendee in event['attendees']:
                if 'self' not in attendee:
                    xstr = "%s    %s: <%s>\n" % (
                        detailsIndent,
                        attendee.get('displayName', 'Not Provided').strip(),
                        attendee.get('email', 'Not Provided').strip()
                    )
                    self.color_printer.msg(xstr, 'default')

        if self.details['attachments'] and 'attachments' in event:
            xstr = "%s  Attachments:\n" % (detailsIndent)
            self.color_printer.msg(xstr, 'default')

            for attendee in event['attachments']:
                xstr = "%s    %s\n%s    -> %s\n" % (
                    detailsIndent,
                    attendee.get('title', 'Not Provided').strip(),
                    detailsIndent,
                    attendee.get('fileUrl', 'Not Provided').strip()
                )
                self.color_printer.msg(xstr, 'default')

        if self.details['length']:
            diffDateTime = (event['e'] - event['s'])
            xstr = "%s  Length: %s\n" % (detailsIndent, diffDateTime)
            self.color_printer.msg(xstr, 'default')

        if self.details['reminders'] and 'reminders' in event:
            if event['reminders']['useDefault'] is True:
                xstr = "%s  Reminder: (default)\n" % (detailsIndent)
                self.color_printer.msg(xstr, 'default')
            elif 'overrides' in event['reminders']:
                for rem in event['reminders']['overrides']:
                    xstr = "%s  Reminder: %s %d minutes\n" % \
                           (detailsIndent, rem['method'], rem['minutes'])
                    self.color_printer.msg(xstr, 'default')

        if self.details['email'] and \
           'email' in event['creator'] and \
           event['creator']['email'].strip():
            xstr = "%s  Email: %s\n" % (
                detailsIndent,
                event['creator']['email'].strip()
            )
            self.color_printer.msg(xstr, 'default')

        if self.details['description'] and \
           'description' in event and \
           event['description'].strip():
            descrIndent = detailsIndent + '  '
            box = True  # leave old non-box code for option later
            if box:
                topMarker = (descrIndent +
                             str(ART_ULC()) +
                             (str(ART_HRZ()) *
                              ((self.details['width'] - len(descrIndent)) -
                               2)) +
                             str(ART_URC()))
                botMarker = (descrIndent +
                             str(ART_LLC()) +
                             (str(ART_HRZ()) *
                              ((self.details['width'] - len(descrIndent)) -
                               2)) +
                             str(ART_LRC()))
                xstr = "%s  Description:\n%s\n%s\n%s\n" % (
                    detailsIndent,
                    topMarker,
                    _formatDescr(event['description'].strip(),
                                 descrIndent, box),
                    botMarker
                )
            else:
                marker = descrIndent + '-' * \
                    (self.details['width'] - len(descrIndent))
                xstr = "%s  Description:\n%s\n%s\n%s\n" % (
                    detailsIndent,
                    marker,
                    _formatDescr(event['description'].strip(),
                                 descrIndent, box),
                    marker
                )
            self.color_printer.msg(xstr, 'default')

    def _DeleteEvent(self, event):

        if self.iamaExpert:
            self._RetryWithBackoff(
                self._CalService().events().
                delete(calendarId=event['gcalcli_cal']['id'],
                       eventId=event['id']))
            self.color_printer.msg('Deleted!\n', 'red')
            return

        PrintMsg('Delete? [N]o [y]es [q]uit: ', 'magenta')
        val = six.moves.input()

        if not val or val.lower() == 'n':
            return

        elif val.lower() == 'y':
            self._RetryWithBackoff(
                self._CalService().events().
                delete(calendarId=event['gcalcli_cal']['id'],
                       eventId=event['id']))
            self.color_printer.msg('Deleted!\n', 'red')

        elif val.lower() == 'q':
            sys.stdout.write('\n')
            sys.exit(0)

        else:
            self.color_printer.err_msg('Error: invalid input\n')
            sys.stdout.write('\n')
            sys.exit(1)

    def _SetEventStartEnd(self, start, end, event):
        event['s'] = parse(start)
        event['e'] - parse(end)

        if self.options['allday']:
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

    def _EditEvent(self, event):

        while True:

            self.color_printer.msg('Edit?\n' +
                              '[N]o [s]ave [q]uit ' +
                              '[t]itle [l]ocation ' +
                              '[w]hen len[g]th ' +
                              '[r]eminder [d]escr: ', 'magenta')
            val = six.moves.input()

            if not val or val.lower() == 'n':
                return

            elif val.lower() == 's':
                # copy only editable event details for patching
                modEvent = {}
                keys = ['summary', 'location', 'start', 'end', 'reminders',
                        'description']
                for k in keys:
                    if k in event:
                        modEvent[k] = event[k]

                self._RetryWithBackoff(
                    self._CalService().events().
                    patch(calendarId=event['gcalcli_cal']['id'],
                          eventId=event['id'],
                          body=modEvent))
                self.color_printer.msg("Saved!\n", 'red')
                return

            elif not val or val.lower() == 'q':
                sys.stdout.write('\n')
                sys.exit(0)

            elif val.lower() == 't':
                self.color_printer.msg('Title: ', 'magenta')
                val = six.moves.input()
                if val.strip():
                    event['summary'] = _u(val.strip())

            elif val.lower() == 'l':
                self.color_printer.msg('Location: ', 'magenta')
                val = six.moves.input()
                if val.strip():
                    event['location'] = _u(val.strip())

            elif val.lower() == 'w':
                self.color_printer.msg('When: ', 'magenta')
                val = six.moves.input().strip()
                if val:
                    td = (event['e'] - event['s'])
                    length = ((td.days * 1440) + (td.seconds / 60))
                    try:
                        newStart, newEnd = GetTimeFromStr(
                                val, length, self.options['allday'])
                    except ValueError as exc:
                        self.color_printer.err_msg(str(exc))
                        sys.exit(1)
                    event = self._SetEventStartEnd(newStart, newEnd, event)

            elif val.lower() == 'g':
                self.color_printer.msg('Length (mins): ', 'magenta')
                val = six.moves.input().strip()
                if val:
                    try:
                        newStart, newEnd = GetTimeFromStr(
                                event['start']['dateTime'], val,
                                self.options['allday'])
                    except ValueError as exc:
                        self.color_printer.err_msg(str(exc))

            elif val.lower() == 'r':
                rem = []
                while 1:
                    self.color_printer.msg(
                            'Enter a valid reminder or \'.\' to end: ',
                            'magenta')
                    r = six.moves.input()
                    if r == '.':
                        break
                    rem.append(r)

                if rem or not self.options['default_reminders']:
                    event['reminders'] = {'useDefault': False,
                                          'overrides': []}
                    for r in rem:
                        n, m = ParseReminder(r)
                        event['reminders']['overrides'].append({'minutes': n,
                                                                'method': m})
                else:
                    event['reminders'] = {'useDefault': True,
                                          'overrides': []}

            elif val.lower() == 'd':
                self.color_printer.msg('Description: ', 'magenta')
                val = six.moves.input()
                if val.strip():
                    event['description'] = _u(val.strip())

            else:
                self.color_printer.err_msg('Error: invalid input\n')
                sys.stdout.write('\n')
                sys.exit(1)

            self._PrintEvent(
                    event, event['s'].strftime('\n%Y-%m-%d'))

    def _IterateEvents(self, startDateTime, eventList,
                       yearDate=False, work=None):

        if len(eventList) == 0:
            self.color_printer.msg('\nNo Events Found...\n', 'yellow')
            return

        # 10 chars for day and length must match 'indent' in _PrintEvent
        dayFormat = '\n%Y-%m-%d' if yearDate else '\n%a %b %d'
        day = ''

        for event in eventList:

            if self.options['ignore_started'] and (event['s'] < self.now):
                continue
            if self.options['ignore_declined'] and self._DeclinedEvent(event):
                continue

            tmpDayStr = event['s'].strftime(dayFormat)
            prefix = None
            if yearDate or tmpDayStr != day:
                day = prefix = tmpDayStr

            self._PrintEvent(event, prefix)

            if work:
                work(event)

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

                event['s'] = self._LocalizeDateTime(event['s'])

                if 'dateTime' in event['end']:
                    event['e'] = parse(event['end']['dateTime'])
                else:
                    # all date events
                    event['e'] = parse(event['end']['date'])

                event['e'] = self._LocalizeDateTime(event['e'])

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
                events = self._RetryWithBackoff(
                    self._CalService().events().
                    list(calendarId=cal['id'], pageToken=pageToken))
            else:
                break

        return eventList

    def _SearchForCalEvents(self, start, end, searchText):

        eventList = []
        for cal in self.cals:
            work = self._CalService().events().\
                list(calendarId=cal['id'],
                     timeMin=start.isoformat() if start else None,
                     timeMax=end.isoformat() if end else None,
                     q=searchText if searchText else None,
                     singleEvents=True)
            events = self._RetryWithBackoff(work)
            eventList.extend(self._GetAllEvents(cal, events, end))

        eventList.sort(key=lambda x: x['s'])

        return eventList

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

        self.color_printer.msg(format % ('Access', 'Title'), 'brightyellow')
        self.color_printer.msg(format % ('------', '-----'), 'brightyellow')

        for cal in self.allCals:
            self.color_printer.msg(
                    format % (cal['accessRole'], cal['summary']),
                    self._CalendarColor(cal))

    def _ParseStartEnd(self, startText, endText):
        start = None
        end = None

        if not startText:
            start = self.now if self.options['ignore_started'] else None
        else:
            try:
                start = self.dateParser.fromString(startText)
            except Exception:
                raise Exception('Error: failed to parse start time\n')

        if endText:
            try:
                end = self.dateParser.fromString(endText)
            except Exception:
                raise Exception('Error: failed to parse end time\n')

        return (start, end)

    def _DisplayQueriedEvents(self, start, end, search=None, yearDate=False):
        eventList = self._SearchForCalEvents(start, end, search)

        if self.options['tsv']:
            self._tsv(start, eventList)
        else:
            self._IterateEvents(start, eventList, yearDate=yearDate)

    def TextQuery(self, searchText='', startText='', endText=''):

        # the empty string would get *ALL* events...
        if not searchText:
            return

        # This is really just an optimization to the gcalendar api
        # why ask for a bunch of events we are going to filter out
        # anyway?
        # TODO: Look at moving this into the _SearchForCalEvents
        #       Don't forget to clean up AgendaQuery too!

        try:
            start, end = self._ParseStartEnd(startText, endText)
        except Exception as exc:
            self.color_printer.err_msg(str(exc))
            return

        self._DisplayQueriedEvents(start, end, searchText, True)

    def AgendaQuery(self, startText='', endText=''):
        try:
            start, end = self._ParseStartEnd(startText, endText)
        except Exception as e:
            self.color_printer.err_msg(str(exc))
            return

        if not start:
            start = self.now.replace(hour=0, minute=0, second=0, microsecond=0)

        if not end:
            end = (start + timedelta(days=self.agendaLength))

        self._DisplayQueriedEvents(start, end)

    def CalQuery(self, cmd, startText='', count=1):

        if not startText:
            # convert now to midnight this morning and use for default
            start = self.now.replace(hour=0,
                                     minute=0,
                                     second=0,
                                     microsecond=0)
        else:
            try:
                start = self.dateParser.fromString(startText)
                start = start.replace(hour=0, minute=0, second=0,
                                      microsecond=0)
            except Exception:
                self.color_printer.err_msg(
                        'Error: failed to parse start time\n')
                return

        # convert start date to the beginning of the week or month
        if cmd == 'calw':
            dayNum = int(start.strftime("%w"))
            if self.options['cal_monday']:
                dayNum -= 1
                if dayNum < 0:
                    dayNum = 6
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

        eventList = self._SearchForCalEvents(start, end, None)

        self._GraphEvents(cmd, start, count, eventList)

    def QuickAddEvent(self, eventText, reminder=None):

        if not eventText:
            return

        if len(self.cals) > 1:
            self.color_printer.err_msg(
                    'You must only specify a single calendar\n')
            return

        if len(self.cals) < 1:
            self.color_printer.err_msg(
                    "Calendar not specified or not found.\n"
                    "If \"gcalcli list\" doesn't find the calendar you're"
                    "trying to use,\n" "your cache file might be stale and"
                    "you might need to remove it and try" "again\n")
            return

        newEvent = self._RetryWithBackoff(
            self._CalService().events().quickAdd(calendarId=self.cals[0]['id'],
                                                 text=eventText))

        if reminder or not self.options['default_reminders']:
            rem = {}
            rem['reminders'] = {'useDefault': False,
                                'overrides': []}
            for r in reminder:
                n, m = ParseReminder(r)
                rem['reminders']['overrides'].append({'minutes': n,
                                                      'method': m})

            newEvent = self._RetryWithBackoff(
                self._CalService().events().
                patch(calendarId=self.cals[0]['id'],
                      eventId=newEvent['id'],
                      body=rem))

        if self.details['url']:
            hLink = self._ShortenURL(newEvent['htmlLink'])
            self.color_printer.msg('New event added: %s\n' % hLink, 'green')

    def AddEvent(self, eTitle, eWhere, eStart, eEnd, eDescr, eWho, reminder):

        if len(self.cals) != 1:
            self.color_printer.err_msg('Must specify a single calendar\n')
            return

        event = {}
        event['summary'] = _u(eTitle)

        if self.options['allday']:
            event['start'] = {'date': eStart}
            event['end'] = {'date': eEnd}

        else:
            event['start'] = {'dateTime': eStart,
                              'timeZone': self.cals[0]['timeZone']}
            event['end'] = {'dateTime': eEnd,
                            'timeZone': self.cals[0]['timeZone']}

        if eWhere:
            event['location'] = _u(eWhere)
        if eDescr:
            event['description'] = _u(eDescr)

        event['attendees'] = list(map(lambda w: {'email': _u(w)}, eWho))

        if reminder or not self.options['default_reminders']:
            event['reminders'] = {'useDefault': False,
                                  'overrides': []}
            for r in reminder:
                n, m = ParseReminder(r)
                event['reminders']['overrides'].append({'minutes': n,
                                                        'method': m})

        newEvent = self._RetryWithBackoff(
            self._CalService().events().
            insert(calendarId=self.cals[0]['id'], body=event))

        if self.details['url']:
            hLink = self._ShortenURL(newEvent['htmlLink'])
            self.color_printer.msg('New event added: %s\n' % hLink, 'green')

    def DeleteEvents(self, searchText='', expert=False, start=None, end=None):

        # the empty string would get *ALL* events...
        if not searchText:
            return

        eventList = self._SearchForCalEvents(start, end, searchText)

        self.iamaExpert = expert
        self._IterateEvents(self.now, eventList,
                            yearDate=True, work=self._DeleteEvent)

    def EditEvents(self, searchText=''):

        # the empty string would get *ALL* events...
        if not searchText:
            return

        eventList = self._SearchForCalEvents(None, None, searchText)

        self._IterateEvents(self.now, eventList,
                            yearDate=True, work=self._EditEvent)

    def Remind(self, minutes=10, command=None, use_reminders=False):
        """Check for events between now and now+minutes.  If use_reminders then
           only remind if now >= event['start'] - reminder"""

        if command is None:
            command = self.command

        # perform a date query for now + minutes + slip
        start = self.now
        end = (start + timedelta(minutes=(minutes + 5)))

        eventList = self._SearchForCalEvents(start, end, None)

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

            if self.options['military']:
                tmpTimeStr = event['s'].strftime('%H:%M')
            else:
                tmpTimeStr = \
                    event['s'].strftime('%I:%M').lstrip('0') + \
                    event['s'].strftime('%p').lower()

            message += '%s  %s\n' % \
                       (tmpTimeStr, _u(self._ValidTitle(event).strip()))

        if not message:
            return

        cmd = shlex.split(command)

        for i, a in zip(range(len(cmd)), cmd):
            if a == '%s':
                cmd[i] = message

        pid = os.fork()
        if not pid:
            os.execvp(cmd[0], cmd)

    def ImportICS(self, verbose=False, dump=False, reminder=None,
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
                self.color_printer.err_msg(
                        'Error: event does not have a dtstart and dtend!\n')
                return None

            if verbose:
                if ve.dtstart.value:
                    print("Start........%s" % ve.dtstart.value.isoformat())
                if ve.dtend.value:
                    print("End..........%s" % ve.dtend.value.isoformat())
                if ve.dtstart.value:
                    print("Local Start..%s" % self._LocalizeDateTime(
                        ve.dtstart.value))
                if ve.dtend.value:
                    print("Local End....%s" % self._LocalizeDateTime(
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

                if reminder or not self.options['default_reminders']:
                    event['reminders'] = {'useDefault': False,
                                          'overrides': []}
                    for r in reminder:
                        n, m = ParseReminder(r)
                        event['reminders']['overrides'].append({'minutes': n,
                                                                'method': m})

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
        except Exception:
            self.color_printer.err_msg(
                    'Python vobject module not installed!\n')
            sys.exit(1)

        if dump:
            verbose = True

        if not dump and len(self.cals) != 1:
            self.color_printer.err_msg('Must specify a single calendar\n')
            return

        f = sys.stdin

        if icsFile:
            try:
                f = open(icsFile)
            except Exception as e:
                self.color_printer.err_msg('Error: ' + str(e) + '!\n')
                sys.exit(1)

        while True:
            try:
                v = vobject.readComponents(f).next()
            except StopIteration:
                break

            for ve in v.vevent_list:

                event = CreateEventFromVOBJ(ve)

                if not event:
                    continue

                if dump:
                    continue

                if not verbose:
                    newEvent = self._RetryWithBackoff(
                        self._CalService().events().
                        insert(calendarId=self.cals[0]['id'],
                               body=event))
                    hLink = self._ShortenURL(newEvent['htmlLink'])
                    PrintMsg(COLORS['green'], 'New event added: %s\n' % hLink)
                    continue

                self.color_printer.msg('\n[S]kip [i]mport [q]uit: ', 'magenta')
                val = six.moves.input()
                if not val or val.lower() == 's':
                    continue
                if val.lower() == 'i':
                    newEvent = self._RetryWithBackoff(
                        self._CalService().events().
                        insert(calendarId=self.cals[0]['id'],
                               body=event))
                    hLink = self._ShortenURL(newEvent['htmlLink'])
                    self.color_printer.msg(
                            'New event added: %s\n' % hLink, 'green')
                elif val.lower() == 'q':
                    sys.exit(0)
                else:
                    self.color_printer.err_msg('Error: invalid input\n')
                    sys.exit(1)


def GetCalColors(calNames):
    calColors = {}
    for calName in calNames:
        calNameParts = calName.split("#")
        calNameSimple = calNameParts[0]
        calColor = calColors.get(calNameSimple)
        if len(calNameParts) > 0:
            calColorRaw = calNameParts[-1]
            calColorNew = calColorRaw
            if calColorNew is not None:
                calColor = calColorNew
        calColors[calNameSimple] = calColor
    return calColors


def ValidWidth(value):
    if type(value) == int and value < 10:
        raise argparse.ArgumentTypeError("Width must be a number >= 10")
    else:
        return int(value)


def ValidReminder(value):
    if not ParseReminder(value):
        raise argparse.ArgumentTypeError(
                "Not a valid reminder string: %s" % value)
    else:
        return value


def get_details_parser():
    details_parser = argparse.ArgumentParser(add_help=False)
    details_parser.add_argument(
            "--details", default=[], type=str, action="append",
            choices=DETAILS,
            help="Which parts to display, can be: " + ", ".join(DETAILS))
    return details_parser


def get_output_parser():
    output_parser = argparse.ArgumentParser(add_help=False)
    output_parser.add_argument(
            "--tsv", action="store_true", dest="tsv", default=False,
            help="Use Tab Separated Value output")
    output_parser.add_argument(
            "--nostarted", action="store_true", dest="ignore_started",
            default=False, help="Hide events that have started")
    output_parser.add_argument(
            "--nodeclined", action="store_true", dest="ignore_declined",
            default=False, help="Hide events that have been declined")
    output_parser.add_argument(
            "--width", "-w", default=10, dest='cal_width', type=ValidWidth,
            help="Set output width")
    output_parser.add_argument(
            "--military", action="store_true", default=False,
            help="Use 24 hour display")
    return output_parser


def get_color_parser():
    color_parser = argparse.ArgumentParser(add_help=False)
    color_parser.add_argument(
            "--color_owner", default="cyan", type=valid_color_name,
            help="Color for owned calendars")
    color_parser.add_argument(
            "--color_writer", default="green", type=valid_color_name,
            help="Color for writable calendars")
    color_parser.add_argument(
            "--color_reader", default="magenta", type=valid_color_name,
            help="Color for read-only calendars")
    color_parser.add_argument(
            "--color_freebusy", default="default", type=valid_color_name,
            help="Color for free/busy calendars")
    color_parser.add_argument(
            "--color_date", default="yellow", type=valid_color_name,
            help="Color for the date")
    color_parser.add_argument(
            "--color_now_marker", default="brightred", type=valid_color_name,
            help="Color for the now marker")
    color_parser.add_argument(
            "--color_border", default="white", type=valid_color_name,
            help="Color of line borders")
    return color_parser


def get_remind_parser():
    remind_parser = argparse.ArgumentParser(add_help=False)
    remind_parser.add_argument(
            "--reminder", default=[], type=ValidReminder, action="append",
            help="Reminders in the form 'TIME METH' or 'TIME'.  TIME "
            "is a number which may be followed by an optional "
            "'w', 'd', 'h', or 'm' (meaning weeks, days, hours, "
            "minutes) and default to minutes.  METH is a string "
            "'popup', 'email', or 'sms' and defaults to popup.")
    remind_parser.add_argument(
            "--default_reminders", action="store_true",
            dest="default_reminders", default=False,
            help="If no --reminder is given, use the defaults.  If this is "
            "false, do not create any reminders.")
    return remind_parser


def get_argument_parser():
    parser = argparse.ArgumentParser(
            description='Google Calendar Command Line Interface',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            fromfile_prefix_chars="@",
            parents=[tools.argparser])

    parser.add_argument(
            "--version", action="version", version="%%(prog)s %s (%s)" %
            (__version__, __author__))

    # Program level options
    parser.add_argument(
            "--client_id", default=__API_CLIENT_ID__, type=str,
            help="API client_id")
    parser.add_argument(
            "--client_secret", default=__API_CLIENT_SECRET__, type=str,
            help="API client_secret")
    parser.add_argument(
            "--configFolder", default=None, type=str,
            help="Optional directory to load/store all configuration " +
            "information")
    parser.add_argument(
            "--noincluderc", action="store_false", dest="includeRc",
            help="Whether to include ~/.gcalclirc when using configFolder")
    parser.add_argument(
            "--calendar", default=[], type=str, action="append",
            help="Which calendars to use")
    parser.add_argument(
            "--defaultCalendar", default=[], type=str, action="append",
            help="Optional default calendar to use if no --calendar options" +
            "are given")
    parser.add_argument(
            "--locale", default=None, type=str, help="System locale")
    parser.add_argument(
            "--refresh", action="store_true", dest="refresh_cache",
            default=False, help="Delete and refresh cached data")
    parser.add_argument(
            "--nocache", action="store_false", dest="use_cache", default=True,
            help="Execute command without using cache")
    parser.add_argument(
            "--conky", action="store_true", default=False,
            help="Use Conky color codes")
    parser.add_argument(
            "--nocolor", action="store_false", default=True, dest="color",
            help="Enable/Disable all color output")
    parser.add_argument(
            "--nolineart", action="store_false", dest="lineart",
            help="Enable/Disable line art")

    # parent parser types used for subcommands
    details_parser = get_details_parser()
    output_parser = get_output_parser()
    color_parser = get_color_parser()
    remind_parser = get_remind_parser()

    sub = parser.add_subparsers(
            help="Invoking a subcommand with --help prints subcommand usage.",
            dest="command")
    sub.required = True

    sub.add_parser("list", parents=[color_parser])

    search = sub.add_parser(
            "search", parents=[details_parser, output_parser, color_parser])
    search.add_argument("text", nargs=1)
    search.add_argument("start", type=str, nargs="?")
    search.add_argument("end", type=str, nargs="?")

    agenda = sub.add_parser(
            "agenda", parents=[details_parser, output_parser, color_parser])
    agenda.add_argument("start", type=str, nargs="?")
    agenda.add_argument("end", type=str, nargs="?")

    calw = sub.add_parser(
            "calw", parents=[details_parser, output_parser, color_parser])
    calw.add_argument("weeks", type=int, default=1, nargs="?")
    calw.add_argument("start", type=str, nargs="?")
    calw.add_argument(
            "--monday", action="store_true", dest='cal_monday', default=False,
            help="Start the week on Monday")
    calw.add_argument(
            "--noweekend", action="store_false", dest='cal_weekend',
            default=True,  help="Hide Saturday and Sunday")

    calm = sub.add_parser(
            "calm", parents=[details_parser, output_parser, color_parser])
    calm.add_argument("start", type=str, nargs="?")
    calm.add_argument(
            "--monday", action="store_true", dest='cal_monday', default=False,
            help="Start the week on Monday")
    calm.add_argument(
            "--noweekend", action="store_false", dest='cal_weekend',
            default=True,  help="Hide Saturday and Sunday")

    quick = sub.add_parser("quick", parents=[details_parser, remind_parser])
    quick.add_argument("text")

    add = sub.add_parser("add", parents=[details_parser, remind_parser])
    add.add_argument("--title", default=None, type=str, help="Event title")
    add.add_argument(
            "--who", default=[], type=str, action="append", help="Event title")
    add.add_argument("--where", default=None, type=str, help="Event location")
    add.add_argument("--when", default=None, type=str, help="Event time")
    add.add_argument(
            "--duration", default=None, type=int,
            help="Event duration in minutes or days if --allday is given.")
    add.add_argument(
            "--description", default=None, type=str, help="Event description")
    add.add_argument(
            "--allday", action="store_true", dest="allday", default=False,
            help="If --allday is given, the event will be an all-day event "
            "(possibly multi-day if --duration is greater than 1). The "
            "time part of the --when will be ignored.")
    add.add_argument(
            "--prompt", action="store_true",
            help="Prompt for missing data when adding events")

    # TODO: Fix this it doesn't work this way as nothing ever goes into [start]
    # or [end]
    delete = sub.add_parser("delete")
    delete.add_argument("text", nargs=1)
    delete.add_argument("start", type=str, nargs="?")
    delete.add_argument("end", type=str, nargs="?")
    delete.add_argument(
            "--iamaexpert", action="store_true", help="Probably not")

    edit = sub.add_parser("edit", parents=[details_parser, output_parser])
    edit.add_argument("text")

    _import = sub.add_parser("import", parents=[remind_parser])
    _import.add_argument("file", type=argparse.FileType('r'), nargs="?")
    _import.add_argument(
            "--verbose", "-v", action="count", help="Be verbose on imports")
    _import.add_argument(
            "--dump", "-d", action="store_true",
            help="Print events and don't import")

    remind = sub.add_parser("remind")
    remind.add_argument("minutes", type=int)
    remind.add_argument("cmd", type=str)
    remind.add_argument(
            "--use_reminders", action="store_true",
            help="Honour the remind time when running remind command")

    return parser


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


    color_printer = ColorPrinter(conky=FLAGS.conky, use_color=FLAGS.color)

    if junk:
        color_printer.err_msg(
                "The following options are either no longer valid globally "
                "or just plain invalid:\n  %s\n" % "\n  ".join(junk))

    if not FLAGS.lineart:
        ART.useArt = False

    if FLAGS.locale:
        try:
            locale.setlocale(locale.LC_ALL, FLAGS.locale)
        except Exception as e:
            color_printer.err_msg(
                    'Error: ' + str(e) +
                    '!\n Check supported locales of your system.\n')
            sys.exit(1)

    if len(FLAGS.calendar) == 0:
        FLAGS.calendar = FLAGS.defaultCalendar

    calNames = []
    calNameColors = []
    calColors = GetCalColors(FLAGS.calendar)
    calNamesFiltered = []
    for calName in FLAGS.calendar:
        calNameSimple = calName.split("#")[0]
        calNamesFiltered.append(_u(calNameSimple))
        calNameColors.append(calColors[calNameSimple])
    calNames = calNamesFiltered

    gcal = GoogleCalendarInterface(calNames=calNames,
                                   calNameColors=calNameColors,
                                   color_printer=color_printer,
                                   **vars(FLAGS))

    if FLAGS.command == 'list':
        gcal.ListAllCalendars()

    elif FLAGS.command == 'search':
        if not FLAGS.text:
            color_printer.err_msg('Error: invalid search string\n')
            sys.exit(1)

        gcal.TextQuery(
                _u(FLAGS.text[0]), startText=FLAGS.start, endText=FLAGS.end)

        if not FLAGS.tsv:
            sys.stdout.write('\n')

    elif FLAGS.command == 'agenda':
        gcal.AgendaQuery(startText=FLAGS.start, endText=FLAGS.end)

        if not FLAGS.tsv:
            sys.stdout.write('\n')

    elif FLAGS.command == 'calw':
        gcal.CalQuery(FLAGS.command, count=FLAGS.weeks, startText=FLAGS.start)
        sys.stdout.write('\n')

    elif FLAGS.command == 'calm':
        gcal.CalQuery(FLAGS.command, startText=FLAGS.start)
        sys.stdout.write('\n')

    elif FLAGS.command == 'quick':
        if not FLAGS.text:
            color_printer.err_msg('Error: invalid event text\n')
            sys.exit(1)

        # allow unicode strings for input
        gcal.QuickAddEvent(_u(FLAGS.text),
                           reminder=FLAGS.reminder)

    elif FLAGS.command == 'add':
        if FLAGS.prompt:
            if FLAGS.title is None:
                color_printer.msg('Title: ', 'magenta')
                FLAGS.title = six.moves.input()
            if FLAGS.where is None:
                color_printer.msg('Location: ', 'magenta')
                FLAGS.where = six.moves.input()
            if FLAGS.when is None:
                color_printer.msg('When: ', 'magenta')
                FLAGS.where = six.moves.input()
            if FLAGS.duration is None:
                if FLAGS.allday:
                    prompt = 'Duration (days): '
                else:
                    prompt = 'Duration (days): '
                color_printer.msg(prmopt, 'magenta')
                FLAGS.duration = six.moves.input()
            if FLAGS.description is None:
                color_printer.msg('Description: ', 'magenta')
                FLAGS.description = six.moves.input()
            if not FLAGS.reminder:
                while 1:
                    color_printer.msg(
                            'Enter a valid reminder or \'.\' to end: ',
                            'magenta')
                    r = six.moves.input()
                    if r == '.':
                        break
                    n, m = ParseReminder(str(r))
                    FLAGS.reminder.append(str(n) + ' ' + m)

        # calculate "when" time:
        try:
            eStart, eEnd = GetTimeFromStr(
                    FLAGS.when, FLAGS.duration, FLAGS.allday)
        except ValueError as exc:
            color_printer.err_msg(str(exc))

        gcal.AddEvent(FLAGS.title, FLAGS.where, eStart, eEnd,
                      FLAGS.description, FLAGS.who,
                      FLAGS.reminder)

    elif FLAGS.command == 'delete':
        eStart = None
        eEnd = None
        if not FLAGS.text:
            color_printer.err_msg('Error: invalid search string\n')
            sys.exit(1)

        if FLAGS.start:
            eStart = gcal.dateParser.fromString(FLAGS.start)
        if FLAGS.end:
            eEnd = gcal.dateParser.fromString(FLAGS.end)

        # allow unicode strings for input
        gcal.DeleteEvents(_u(FLAGS.text[0]),
                          FLAGS.iamaexpert, eStart, eEnd)

        sys.stdout.write('\n')

    elif FLAGS.command == 'edit':
        if not FLAGS.text:
            color_printer.err_msg('Error: invalid search string\n')
            sys.exit(1)

        # allow unicode strings for input
        gcal.EditEvents(_u(FLAGS.text))

        sys.stdout.write('\n')

    elif FLAGS.command == 'remind':
        gcal.Remind(
                FLAGS.minutes, FLAGS.cmd, use_reminders=FLAGS.use_reminders)

    elif FLAGS.command == 'import':
        gcal.ImportICS(
                FLAGS.verbose, FLAGS.dump, FLAGS.reminder, FLAGS.file.name)


def SIGINT_handler(signum, frame):
    sys.stderr.write('Signal caught, bye!\n')
    sys.exit(1)


signal.signal(signal.SIGINT, SIGINT_handler)


if __name__ == '__main__':
    main()
