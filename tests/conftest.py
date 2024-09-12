import os
import sys
from datetime import datetime, timedelta
from types import SimpleNamespace

import google.oauth2.reauth
import pytest
from dateutil.tz import tzlocal
from googleapiclient.discovery import HttpMock, build

from gcalcli.argparsers import (get_cal_query_parser, get_color_parser,
                                get_output_parser)
from gcalcli.gcal import GoogleCalendarInterface
from gcalcli.printer import Printer

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
def PatchedGCalIForEvents(PatchedGCalI, monkeypatch):
    def mocked_search_for_events(self, start, end, search_text):
        return mock_event

    monkeypatch.setattr(
        GoogleCalendarInterface, '_search_for_events', mocked_search_for_events
    )

    return PatchedGCalI


@pytest.fixture
def PatchedGCalI(gcali_patches):
    gcali_patches.stub_out_cal_service()
    return gcali_patches.GCalI


@pytest.fixture
def gcali_patches(monkeypatch):
    def mocked_cal_service(self):
        http = HttpMock(
            TEST_DATA_DIR + '/cal_service_discovery.json', {'status': '200'}
        )
        if not self.cal_service:
            self.cal_service = build(
                serviceName='calendar', version='v3', http=http
            )
        return self.cal_service

    def mocked_calendar_list(self):
        http = HttpMock(TEST_DATA_DIR + '/cal_list.json', {'status': '200'})
        request = self.get_cal_service().calendarList().list()
        cal_list = request.execute(http=http)
        self.all_cals = [cal for cal in cal_list['items']]
        if not self.cal_service:
            self.cal_service = build(
                serviceName='calendar', version='v3', http=http
            )
        return self.cal_service

    def mocked_msg(self, msg, colorname='default', file=sys.stdout):
        # ignores file and always writes to stdout
        if self.use_color:
            msg = self.colors[colorname] + msg + self.colors['default']
        sys.stdout.write(msg)

    monkeypatch.setattr(
        GoogleCalendarInterface, '_get_cached', mocked_calendar_list
    )
    monkeypatch.setattr(Printer, 'msg', mocked_msg)

    def data_file_path_stub(self, name):
        stubbed_path = getattr(self, '_stubbed_data_path', None)
        if stubbed_path is None:
            return None
        return stubbed_path.joinpath(name)
    monkeypatch.setattr(
        GoogleCalendarInterface, 'data_file_path', data_file_path_stub)

    orig_init = GoogleCalendarInterface.__init__
    def modified_init(self, *args, data_path=None, **kwargs):
        self._stubbed_data_path = data_path
        kwargs.setdefault('ignore_calendars', [])
        return orig_init(self, *args, **kwargs, use_cache=False)
    monkeypatch.setattr(GoogleCalendarInterface, '__init__', modified_init)

    return SimpleNamespace(
        GCalI=GoogleCalendarInterface,
        stub_out_cal_service=lambda: monkeypatch.setattr(
            GoogleCalendarInterface, 'get_cal_service', mocked_cal_service
        ),
    )


@pytest.fixture
def patched_google_reauth(monkeypatch):
    def mocked_refresh_grant(*args, **kw):
        expiry = datetime.now() + timedelta(minutes=60)
        grant_response = {}
        return (
            'some_access_token',
            'some_refresh_token',
            expiry,
            grant_response,
            'some_rapt_token',
        )

    monkeypatch.setattr(
        google.oauth2.reauth, 'refresh_grant', mocked_refresh_grant
    )
    return monkeypatch
