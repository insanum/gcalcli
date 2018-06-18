import os
import sys
from json import load

import pytest
from apiclient.discovery import HttpMock, build
from gcalcli.color_printer import ColorPrinter
from gcalcli.gcalcli import GoogleCalendarInterface, _u, get_color_parser

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


def mocked_msg(self, msg, colorname, file=sys.stdout):
    # ignores file and always writes to stdout
    if self.use_color:
        msg = self.colors[colorname] + msg + self.colors['default']
    sys.stdout.write(msg)


@pytest.fixture
def default_color_options():
    return get_color_parser().parse_args([])


@pytest.fixture
def gcal(monkeypatch, default_color_options):
    monkeypatch.setattr(
            GoogleCalendarInterface, '_CalService', mocked_calendar_service)
    monkeypatch.setattr(
            GoogleCalendarInterface, '_GetCached', mocked_calendar_list)
    monkeypatch.setattr(ColorPrinter, 'msg', mocked_msg)
    return GoogleCalendarInterface(
            use_cache=False, **vars(default_color_options))


# TODO: These are more like placeholders for proper unit tests
#       We just try the commands and make sure no errors occur.
def test_list(capsys, gcal):
    with open(TEST_DATA_DIR + '/cal_list.json') as cl:
        cal_count = len(load(cl)['items'])

    # test data has 6 cals
    assert cal_count == len(gcal.allCals)
    expected_header = gcal.color_printer.get_colorcode(
            gcal.options['color_title']) + ' Access  Title\n'

    gcal.ListAllCalendars()
    captured = capsys.readouterr()
    assert captured.out.startswith(_u(expected_header))

    # +3 cos one for the header, one for the '----' decorations,
    # and one for the eom
    assert len(captured.out.split('\n')) == cal_count + 3


def test_agenda(gcal):
    gcal.AgendaQuery()


def test_cal_query(gcal):
    gcal.AgendaQuery('calw')
    gcal.AgendaQuery('calm')
