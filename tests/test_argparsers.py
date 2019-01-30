from gcalcli import argparsers
import shlex
import pytest


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


def test_output_parser():
    output_parser = argparsers.get_output_parser()
    argv = shlex.split('-w 9')
    with pytest.raises(SystemExit):
        output_parser.parse_args(argv)

    argv = shlex.split('-w 10')
    assert output_parser.parse_args(argv).cal_width == 10


def test_search_parser():
    search_parser = argparsers.get_search_parser()
    with pytest.raises(SystemExit):
        search_parser.parse_args([])


def test_details_parser():
    details_parser = argparsers.get_details_parser()

    argv = shlex.split('--details attendees --details url --details location')
    parsed_details = details_parser.parse_args(argv).details
    assert parsed_details['attendees']
    assert parsed_details['location']
    assert parsed_details['url'] == 'short'

    argv = shlex.split('--details all')
    parsed_details = details_parser.parse_args(argv).details
    assert all(parsed_details[d] for d in argparsers.BOOL_DETAILS)

    # ensure we can specify url type even with details=all
    argv = shlex.split('--details all --details longurl')
    parsed_details = details_parser.parse_args(argv).details
    assert parsed_details['url'] == 'long'


def test_handle_unparsed():
    # minimal test showing that we can parse a global option after the
    # subcommand (in some cases)
    parser = argparsers.get_argument_parser()
    argv = shlex.split('delete --calendar=test "search text"')
    parsed, unparsed = parser.parse_known_args(argv)
    parsed = argparsers.handle_unparsed(unparsed, parsed)
    assert parsed.calendar == ['test']
