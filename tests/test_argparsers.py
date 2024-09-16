from collections import namedtuple
import shlex

import pytest

from gcalcli import argparsers


def test_get_argparser():
    """Just asserts no errors have been introduced"""
    argparser = argparsers.get_argument_parser()
    assert argparser


def test_reminder_parser():
    remind_parser = argparsers.get_remind_parser()
    argv = shlex.split('--reminder invalid reminder')
    with pytest.raises(SystemExit):
        remind_parser.parse_args(argv)

    argv = shlex.split('--reminder "5m sms"')
    assert len(remind_parser.parse_args(argv).reminders) == 1


def test_output_parser(monkeypatch):
    def sub_terminal_size(columns):
        ts = namedtuple('terminal_size', ['lines', 'columns'])

        def fake_get_terminal_size():
            return ts(123, columns)

        return fake_get_terminal_size

    output_parser = argparsers.get_output_parser()
    argv = shlex.split('-w 9')
    with pytest.raises(SystemExit):
        output_parser.parse_args(argv)

    argv = shlex.split('-w 10')
    assert output_parser.parse_args(argv).cal_width == 10

    argv = shlex.split('')
    monkeypatch.setattr(argparsers, 'get_terminal_size', sub_terminal_size(70))
    output_parser = argparsers.get_output_parser()
    assert output_parser.parse_args(argv).cal_width == 10

    argv = shlex.split('')
    monkeypatch.setattr(argparsers, 'get_terminal_size',
                        sub_terminal_size(100))
    output_parser = argparsers.get_output_parser()
    assert output_parser.parse_args(argv).cal_width == 13


def test_search_parser():
    search_parser = argparsers.get_search_parser()
    with pytest.raises(SystemExit):
        search_parser.parse_args([])


def test_updates_parser():
    updates_parser = argparsers.get_updates_parser()

    argv = shlex.split('2019-07-18 2019-08-01 2019-09-01')
    parsed_updates = updates_parser.parse_args(argv)
    assert parsed_updates.since
    assert parsed_updates.start
    assert parsed_updates.end


def test_conflicts_parser():
    updates_parser = argparsers.get_conflicts_parser()

    argv = shlex.split('search 2019-08-01 2019-09-01')
    parsed_conflicts = updates_parser.parse_args(argv)
    assert parsed_conflicts.text
    assert parsed_conflicts.start
    assert parsed_conflicts.end


def test_details_parser():
    details_parser = argparsers.get_details_parser()

    argv = shlex.split('--details attendees --details url '
                       '--details location --details end')
    parsed_details = details_parser.parse_args(argv).details
    assert parsed_details['attendees']
    assert parsed_details['location']
    assert parsed_details['url']
    assert parsed_details['end']

    argv = shlex.split('--details all')
    parsed_details = details_parser.parse_args(argv).details
    assert all(parsed_details[d] for d in argparsers.DETAILS)


def test_handle_unparsed():
    # minimal test showing that we can parse a global option after the
    # subcommand (in some cases)
    parser = argparsers.get_argument_parser()
    argv = shlex.split('delete --calendar=test "search text"')
    parsed, unparsed = parser.parse_known_args(argv)
    parsed = argparsers.handle_unparsed(unparsed, parsed)
    assert parsed.calendars == ['test']
