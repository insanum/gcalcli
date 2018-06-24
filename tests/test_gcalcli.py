import os
import sys
from json import load

import pytest
from apiclient.discovery import HttpMock, build
from gcalcli.printer import Printer
from gcalcli.gcalcli import (GoogleCalendarInterface, _u,
                             get_color_parser,
                             get_cal_query_parser,
                             get_output_parser,
                             parse_reminder)

TEST_DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + '/data'


def mocked_calendar_service(self):
    http = HttpMock(
            TEST_DATA_DIR + '/cal_service_discovery.json', {'status': '200'})
    if not self.calService:
        self.calService = build(
                serviceName='calendar', version='v3', http=http)
    return self.calService


def mocked_calendar_list(self):
    http = HttpMock(
            TEST_DATA_DIR + '/cal_list.json', {'status': '200'})
    request = self._CalService().calendarList().list()
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


@pytest.fixture
def default_options():
    opts = vars(get_color_parser().parse_args([]))
    opts.update(vars(get_cal_query_parser().parse_args([])))
    opts.update(vars(get_output_parser().parse_args([])))
    return opts


@pytest.fixture
def PatchedGCalI(monkeypatch):
    monkeypatch.setattr(
            GoogleCalendarInterface, '_CalService', mocked_calendar_service)
    monkeypatch.setattr(
            GoogleCalendarInterface, '_GetCached', mocked_calendar_list)
    monkeypatch.setattr(Printer, 'msg', mocked_msg)

    def _method(**opts):
        return GoogleCalendarInterface(use_cache=False, **opts)

    return _method


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
    PatchedGCalI(calendar=['jcrowgey*#green']).AgendaQuery()


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
    gcal = PatchedGCalI(calendar=['jcrowgey*#green'])
    title = 'test event'
    where = 'anywhere'
    start = 'now'
    end = 'tomorrow'
    descr = 'testing'
    who = 'anyone'
    reminder = None
    gcal.AddEvent(title, where, start, end, descr, who, reminder)


def test_quick_add(PatchedGCalI):
    gcal = PatchedGCalI(calendar=['jcrowgey*#green'])
    event_text = 'quick test event'
    reminder = '5m sms'
    gcal.QuickAddEvent(event_text, reminder=[reminder])


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
