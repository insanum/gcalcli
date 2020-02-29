from __future__ import absolute_import

import os
from json import load

from dateutil.tz import tzutc
from datetime import datetime

from gcalcli.utils import parse_reminder
from gcalcli.argparsers import (get_start_end_parser,
                                get_color_parser,
                                get_cal_query_parser,
                                get_output_parser,
                                get_updates_parser,
                                get_conflicts_parser,
                                get_search_parser)
from gcalcli.gcal import GoogleCalendarInterface
from gcalcli.cli import parse_cal_names


TEST_DATA_DIR = os.path.dirname(os.path.abspath(__file__)) + '/data'


# TODO: These are more like placeholders for proper unit tests
#       We just try the commands and make sure no errors occur.
def test_list(capsys, PatchedGCalI):
    gcal = PatchedGCalI(**vars(get_color_parser().parse_args([])))
    with open(TEST_DATA_DIR + '/cal_list.json') as cl:
        cal_count = len(load(cl)['items'])

    # test data has 6 cals
    assert cal_count == len(gcal.all_cals)
    expected_header = gcal.printer.get_colorcode(
            gcal.options['color_title']) + ' Access  Title\n'

    gcal.ListAllCalendars()
    captured = capsys.readouterr()
    assert captured.out.startswith(expected_header)

    # +3 cos one for the header, one for the '----' decorations,
    # and one for the eom
    assert len(captured.out.split('\n')) == cal_count + 3


def test_agenda(PatchedGCalI):
    assert PatchedGCalI().AgendaQuery() == 0

    opts = get_start_end_parser().parse_args(['tomorrow'])
    assert PatchedGCalI().AgendaQuery(start=opts.start, end=opts.end) == 0

    opts = get_start_end_parser().parse_args(['today', 'tomorrow'])
    assert PatchedGCalI().AgendaQuery(start=opts.start, end=opts.end) == 0


def test_updates(PatchedGCalI):
    since = datetime(2019, 7, 10)
    assert PatchedGCalI().UpdatesQuery(since) == 0

    opts = get_updates_parser().parse_args(
            ['2019-07-10', '2019-07-19', '2019-08-01'])
    assert PatchedGCalI().UpdatesQuery(
            last_updated_datetime=opts.since,
            start=opts.start,
            end=opts.end) == 0


def test_conflicts(PatchedGCalI):
    assert PatchedGCalI().ConflictsQuery() == 0

    opts = get_conflicts_parser().parse_args(
            ['search text', '2019-07-19', '2019-08-01'])
    assert PatchedGCalI().ConflictsQuery(
            'search text',
            start=opts.start,
            end=opts.end) == 0


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


def test_declined_event_no_attendees(PatchedGCalI):
    gcal = PatchedGCalI()
    event = {
        'gcalcli_cal': {
            'id': 'user@email.com',
        },
        'attendees': []
    }
    assert not gcal._DeclinedEvent(event)


def test_declined_event_non_matching_attendees(PatchedGCalI):
    gcal = PatchedGCalI()
    event = {
        'gcalcli_cal': {
            'id': 'user@email.com',
        },
        'attendees': [{
            'email': 'user2@otheremail.com',
            'responseStatus': 'declined',
        }]
    }
    assert not gcal._DeclinedEvent(event)


def test_declined_event_matching_attendee_declined(PatchedGCalI):
    gcal = PatchedGCalI()
    event = {
        'gcalcli_cal': {
            'id': 'user@email.com',
        },
        'attendees': [
            {
                'email': 'user@email.com',
                'responseStatus': 'declined',
            },
            {
                'email': 'user2@otheremail.com',
                'responseStatus': 'accepted',
            },
        ]
    }
    assert gcal._DeclinedEvent(event)


def test_declined_event_matching_attendee_accepted(PatchedGCalI):
    gcal = PatchedGCalI()
    event = {
        'gcalcli_cal': {
            'id': 'user@email.com',
        },
        'attendees': [
            {
                'email': 'user@email.com',
                'responseStatus': 'accepted',
            },
            {
                'email': 'user2@otheremail.com',
                'responseStatus': 'declined',
            },
        ]
    }
    assert not gcal._DeclinedEvent(event)


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


def test_next_cut(PatchedGCalI):
    gcal = PatchedGCalI()
    # default width is 10
    test_cal_width = 10
    gcal.options['cal_width'] = test_cal_width
    event_title = "first looooong"
    assert gcal._next_cut(event_title) == (5, 5)

    event_title = "tooooooloooong"
    assert gcal._next_cut(event_title) == (test_cal_width, test_cal_width)

    event_title = "one two three four"
    assert gcal._next_cut(event_title) == (7, 7)

    # event_title = "& G NSW VIM Project"
    # assert gcal._next_cut(event_title) == (7, 7)

    event_title = "樹貞 fun fun fun"
    assert gcal._next_cut(event_title) == (8, 6)
