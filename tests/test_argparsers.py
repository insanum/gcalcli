from gcalcli import argparsers
import pytest


def test_get_argparser():
    """Just asserts no errors have been introduced"""
    argparser = argparsers.get_argument_parser()
    assert argparser


def test_reminder_parser():
    remind_parser = argparsers.get_remind_parser()
    with pytest.raises(SystemExit):
        remind_parser.parse_args(['--reminder', 'invalid reminder'])
    assert \
        len(remind_parser.parse_args(['--reminder', '5m sms']).reminders) == 1


def test_output_parser():
    output_parser = argparsers.get_output_parser()
    with pytest.raises(SystemExit):
        output_parser.parse_args(['-w', '9'])
    assert output_parser.parse_args(['-w', '10']).cal_width == 10


def test_search_parser():
    search_parser = argparsers.get_search_parser()
    with pytest.raises(SystemExit):
        search_parser.parse_args([])


def test_details_parser():
    details_parser = argparsers.get_details_parser()
    parsed_details = details_parser.parse_args(['--details', 'all']).details
    assert set(parsed_details) == set(argparsers.DETAILS) - set(['all'])
