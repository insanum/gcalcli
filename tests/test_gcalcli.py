from __future__ import absolute_import
import os
import sys
from json import load
from datetime import datetime
from dateutil.tz import tzutc, tzlocal

import pytest
from apiclient.discovery import HttpMock, build
from gcalcli.printer import Printer
from gcalcli.utils import parse_reminder, _u
from gcalcli.argparsers import (get_start_end_parser,
                                get_color_parser,
                                get_cal_query_parser,
                                get_output_parser,
                                get_search_parser)
from gcalcli.gcalcli import (GoogleCalendarInterface,
                             parse_cal_names)

TEST_DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + '/data'

mock_event = [{'colorId': "10",
               'created': '2018-12-31T09:20:32.000Z',
               'creator': {'email': 'matthew.lemon@gmail.com'},
               'e': datetime(2019, 1, 8, 15, 15, tzinfo=tzlocal()),
               'end': {'dateTime': '2019-01-08T15:15:00Z'},
               'etag': '"3092496064420000"',
               'gcalcli_cal': {'accessRole': 'owner',
                               'backgroundColor': '#4986e7',
                               'colorId': '16',
                               'conferenceProperties': {
                                   'allowedConferenceSolutionTypes':
                                   ['eventHangout']
                               },
                               'defaultReminders': [],
                               'etag': '"153176133553000"',
                               'foregroundColor': '#000000',
                               'id': '12pp3nqo@group.calendar.google.com',
                               'kind': 'calendar#calendarListEntry',
                               'selected': True,
                               'summary': 'Test Calendar',
                               'timeZone': 'Europe/London'},
               'htmlLink': '',
               'iCalUID': '31376E6-8B63-416C-B73A-74D10F51F',
               'id': '_6coj0c9o88r3b9a26spk2b9n6sojed2464o4cd9h8o',
               'kind': 'calendar#event',
               'organizer': {
                   'displayName': 'Test Calendar',
                   'email': 'tst@group.google.com',
                   'self': True},
               'reminders': {'useDefault': True},
               's': datetime(2019, 1, 8, 14, 15, tzinfo=tzlocal()),
               'sequence': 0,
               'start': {'dateTime': '2019-01-08T14:15:00Z'},
               'status': 'confirmed',
               'summary': 'Test Event',
               'updated': '2018-12-31T09:20:32.210Z'}]


@pytest.fixture
def default_options():
    opts = vars(get_color_parser().parse_args([]))
    opts.update(vars(get_cal_query_parser().parse_args([])))
    opts.update(vars(get_output_parser().parse_args([])))
    return opts


@pytest.fixture
def PatchedGCalIForEvents(monkeypatch):
    def mocked_search_for_events(self, start, end, search_text):
        return mock_event

    def mocked_calendar_service(self):
        http = HttpMock(
                TEST_DATA_DIR + '/cal_service_discovery.json',
                {'status': '200'})
        if not self.calService:
            self.calService = build(
                    serviceName='calendar', version='v3', http=http)
        return self.calService

    def mocked_calendar_list(self):
        http = HttpMock(
                TEST_DATA_DIR + '/cal_list.json', {'status': '200'})
        request = self._cal_service().calendarList().list()
        cal_list = request.execute(http=http)
        self.allCals = [cal for cal in cal_list['items']]
        if not self.calService:
            self.calService = build(
                 serviceName='calendar', version='v3', http=http)
        return self.calService

    def mocked_msg(self, msg, colorname='default', file=sys.stdout):
        # ignores file and always writes to stdout
        if self.use_color:
            msg = self.colors[colorname] + msg + self.colors['default']
        sys.stdout.write(msg)

    monkeypatch.setattr(
            GoogleCalendarInterface, '_search_for_events',
            mocked_search_for_events)
    monkeypatch.setattr(
            GoogleCalendarInterface, '_cal_service', mocked_calendar_service)
    monkeypatch.setattr(
            GoogleCalendarInterface, '_get_cached', mocked_calendar_list)
    monkeypatch.setattr(Printer, 'msg', mocked_msg)

    def _init(**opts):
        return GoogleCalendarInterface(use_cache=False, **opts)

    return _init


@pytest.fixture
def PatchedGCalI(monkeypatch):
    def mocked_calendar_service(self):
        http = HttpMock(
                TEST_DATA_DIR + '/cal_service_discovery.json',
                {'status': '200'})
        if not self.calService:
            self.calService = build(
                    serviceName='calendar', version='v3', http=http)
        return self.calService

    def mocked_calendar_list(self):
        http = HttpMock(
                TEST_DATA_DIR + '/cal_list.json', {'status': '200'})
        request = self._cal_service().calendarList().list()
        cal_list = request.execute(http=http)
        self.allCals = [cal for cal in cal_list['items']]
        if not self.calService:
            self.calService = build(
                 serviceName='calendar', version='v3', http=http)
        return self.calService

    def mocked_msg(self, msg, colorname='default', file=sys.stdout):
        # ignores file and always writes to stdout
        if self.use_color:
            msg = self.colors[colorname] + msg + self.colors['default']
        sys.stdout.write(msg)

    monkeypatch.setattr(
            GoogleCalendarInterface, '_cal_service', mocked_calendar_service)
    monkeypatch.setattr(
            GoogleCalendarInterface, '_get_cached', mocked_calendar_list)
    monkeypatch.setattr(Printer, 'msg', mocked_msg)

    def _init(**opts):
        return GoogleCalendarInterface(use_cache=False, **opts)

    return _init


# TODO: These are more like placeholders for proper unit tests
#       We just try the commands and make sure no errors occur.
def test_list(capsys, PatchedGCalI):
    gcal = PatchedGCalI(**vars(get_color_parser().parse_args([])))
    with open(TEST_DATA_DIR + '/cal_list.json') as cl:
        cal_count = len(load(cl)['items'])

    # test data has 6 cals
    assert cal_count == len(gcal.allCals)
    expected_header = gcal.printer.get_colorcode(
            gcal.options['color_title']) + ' Access  Title\n'

    gcal.ListAllCalendars()
    captured = capsys.readouterr()
    assert captured.out.startswith(_u(expected_header))

    # +3 cos one for the header, one for the '----' decorations,
    # and one for the eom
    assert len(captured.out.split('\n')) == cal_count + 3


def test_agenda(PatchedGCalI):
    assert PatchedGCalI().AgendaQuery() == 0

    opts = get_start_end_parser().parse_args(['tomorrow'])
    assert PatchedGCalI().AgendaQuery(start=opts.start, end=opts.end) == 0

    opts = get_start_end_parser().parse_args(['today', 'tomorrow'])
    assert PatchedGCalI().AgendaQuery(start=opts.start, end=opts.end) == 0


def test_cal_query(capsys, PatchedGCalI):
    opts = vars(get_cal_query_parser().parse_args([]))
    opts.update(vars(get_output_parser().parse_args([])))
    opts.update(vars(get_color_parser().parse_args([])))
    gcal = PatchedGCalI(**opts)

    gcal.CalQuery('calw')
    captured = capsys.readouterr()
    art = gcal.printer.art
    expect_top = (
            gcal.printer.colors[gcal.options['color_border']] + art['ulc'] +
            art['hrz'] * gcal.options['cal_width'])
    assert captured.out.startswith(expect_top)

    gcal.CalQuery('calm')
    captured = capsys.readouterr()
    assert captured.out.startswith(expect_top)


def test_add_event(PatchedGCalI):
    cal_names = parse_cal_names(['jcrowgey@uw.edu'])
    gcal = PatchedGCalI(
            cal_names=cal_names, allday=False, default_reminders=True)
    title = 'test event'
    where = 'anywhere'
    start = 'now'
    end = 'tomorrow'
    descr = 'testing'
    who = 'anyone'
    reminders = None
    color = "banana"
    assert gcal.AddEvent(
        title, where, start, end, descr, who, reminders, color)


def test_add_event_override_color(capsys, default_options,
                                  PatchedGCalIForEvents):
    default_options.update({'override_color': True})
    cal_names = parse_cal_names(['jcrowgey@uw.edu'])
    gcal = PatchedGCalIForEvents(cal_names=cal_names, **default_options)
    gcal.AgendaQuery()
    captured = capsys.readouterr()
    # this could be parameterized with pytest eventually
    # assert colorId 10: green
    assert '\033[0;32m' in captured.out


def test_quick_add(PatchedGCalI):
    cal_names = parse_cal_names(['jcrowgey@uw.edu'])
    gcal = PatchedGCalI(cal_names=cal_names)
    event_text = 'quick test event'
    reminder = '5m sms'
    assert gcal.QuickAddEvent(event_text, reminders=[reminder])


def test_text_query(PatchedGCalI):
    search_parser = get_search_parser()
    gcal = PatchedGCalI()

    # TODO: mock the api reply for the search
    # and then assert something greater than zero

    opts = search_parser.parse_args(['test', '1970-01-01', '2038-01-18'])
    assert gcal.TextQuery(opts.text, opts.start, opts.end) == 0

    opts = search_parser.parse_args(['test', '1970-01-01'])
    assert gcal.TextQuery(opts.text, opts.start, opts.end) == 0

    opts = search_parser.parse_args(['test'])
    assert gcal.TextQuery(opts.text, opts.start, opts.end) == 0


def test_modify_event(PatchedGCalI):
    opts = get_search_parser().parse_args(['test'])
    gcal = PatchedGCalI(**vars(opts))
    assert gcal.ModifyEvents(
            gcal._edit_event, opts.text, opts.start, opts.end) == 0


def test_import(PatchedGCalI):
    cal_names = parse_cal_names(['jcrowgey@uw.edu'])
    gcal = PatchedGCalI(cal_names=cal_names, default_reminders=True)
    vcal_path = TEST_DATA_DIR + '/vv.txt'
    assert gcal.ImportICS(icsFile=open(vcal_path))


def test_parse_reminder():
    MINS_PER_DAY = 60 * 24
    MINS_PER_WEEK = MINS_PER_DAY * 7

    rem = '5m email'
    tim, method = parse_reminder(rem)
    assert method == 'email'
    assert tim == 5

    rem = '2h sms'
    tim, method = parse_reminder(rem)
    assert method == 'sms'
    assert tim == 120

    rem = '1d popup'
    tim, method = parse_reminder(rem)
    assert method == 'popup'
    assert tim == MINS_PER_DAY

    rem = '1w'
    tim, method = parse_reminder(rem)
    assert method == 'popup'
    assert tim == MINS_PER_WEEK

    rem = '10w'
    tim, method = parse_reminder(rem)
    assert method == 'popup'
    assert tim == MINS_PER_WEEK * 10

    rem = 'invalid reminder'
    assert parse_reminder(rem) is None


def test_parse_cal_names(PatchedGCalI):
    # TODO we need to mock the event list returned by the search
    # and then assert the right number of events
    # for the moment, we assert 0 (which indicates successful completion of
    # the code path, but no events printed)
    cal_names = parse_cal_names(['j*#green'])
    gcal = PatchedGCalI(cal_names=cal_names)
    assert gcal.AgendaQuery() == 0

    cal_names = parse_cal_names(['j*'])
    gcal = PatchedGCalI(cal_names=cal_names)
    assert gcal.AgendaQuery() == 0

    cal_names = parse_cal_names(['jcrowgey@uw.edu'])
    gcal = PatchedGCalI(cal_names=cal_names)
    assert gcal.AgendaQuery() == 0


def test_localize_datetime(PatchedGCalI):
    dt = GoogleCalendarInterface._localize_datetime(datetime.now())
    assert dt.tzinfo is not None

    dt = datetime.now(tzutc())
    dt = GoogleCalendarInterface._localize_datetime(dt)
    assert dt.tzinfo is not None


def test_iterate_events(capsys, PatchedGCalI):
    gcal = PatchedGCalI()
    assert gcal._iterate_events(gcal.now, []) == 0

    # TODO: add some events to a list and assert their selection
