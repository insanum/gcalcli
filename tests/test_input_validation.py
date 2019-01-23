import os
import pytest

from gcalcli.validators import validate_input, ValidationError
from gcalcli.validators import (STR_NOT_EMPTY,
                                PARSABLE_DATE,
                                STR_TO_INT,
                                STR_ALLOW_EMPTY,
                                REMINDER,
                                VALID_COLORS)

import gcalcli.validators

# Tests required:
#
# * Title: any string, not blank
# * Location: any string, allow blank
# * When: string that can be parsed by dateutil
# * Duration: string that can be cast to int
# * Description: any string, allow blank
# * Color: any string matching: blueberry, lavendar, grape, etc, or blank
# * Reminder: a valid reminder


def test_any_string_not_blank_validator(monkeypatch):
    # Empty string raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "")
    with pytest.raises(ValidationError):
        validate_input(STR_NOT_EMPTY) == ValidationError(
            "Input here cannot be empty")

    # None raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: None)
    with pytest.raises(ValidationError):
        validate_input(STR_NOT_EMPTY) == ValidationError(
            "Input here cannot be empty")

    # Valid string passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "Valid Text")
    assert validate_input(STR_NOT_EMPTY) == "Valid Text"


def test_any_string_parsable_by_dateutil(monkeypatch):
    # non-date raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "NON-DATE STR")
    with pytest.raises(ValidationError):
        validate_input(PARSABLE_DATE) == ValidationError(
            "Expected format: a date (e.g. 2019-01-01, tomorrow 10am, "
            "2nd Jan, Jan 4th, etc) or valid time if today. "
            "(Ctrl-C to exit)\n"
        )

    # date string passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "2nd January")
    validate_input(PARSABLE_DATE) == "2nd January"


def test_string_can_be_cast_to_int(monkeypatch):
    # non int-castable string raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "X")
    with pytest.raises(ValidationError):
        validate_input(STR_TO_INT) == ValidationError(
            "Input here must be a number")

    # int string passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "10")
    validate_input(STR_TO_INT) == "10"


def test_for_valid_colour_name(monkeypatch):
    # non valid colour raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "purple")
    with pytest.raises(ValidationError):
        validate_input(VALID_COLORS) == ValidationError(
            "purple is not a valid color value to use here. Please "
            "use one of basil, peacock, grape, lavender, blueberry,"
            "tomato, safe, flamingo or banana."
        )
    # valid colour passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "grape")
    validate_input(VALID_COLORS) == "grape"

    # empty str passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "")
    validate_input(VALID_COLORS) == ""


def test_any_string_and_blank(monkeypatch):
    # string passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "TEST")
    validate_input(STR_ALLOW_EMPTY) == "TEST"

    # dot passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: ".")
    validate_input(STR_ALLOW_EMPTY) == "."


def test_reminder(monkeypatch):
    # valid reminders pass
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "10m email")
    validate_input(REMINDER) == "10m email"

    monkeypatch.setattr(gcalcli.validators, "input", lambda: "10 popup")
    validate_input(REMINDER) == "10m email"

    monkeypatch.setattr(gcalcli.validators, "input", lambda: "10m sms")
    validate_input(REMINDER) == "10m email"

    monkeypatch.setattr(gcalcli.validators, "input", lambda: "12323")
    validate_input(REMINDER) == "10m email"

    # invalid reminder raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "meaningless")
    with pytest.raises(ValidationError):
        validate_input(REMINDER) == ValidationError(
            "Format: <number><w|d|h|m> <popup|email|sms>\n")

    # invalid reminder raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "")
    with pytest.raises(ValidationError):
        validate_input(REMINDER) == ValidationError(
            "Format: <number><w|d|h|m> <popup|email|sms>\n")


def test_edit_event_description(capsys, monkeypatch,
                                PatchedGCalIForEvents, default_options):
    # we need a func to pass into gcalcli.validators.validate_input
    def _useless():
        pass
    # we need a way to be able to jump out of the edit loop
    # set an env variable here, then change it after the first
    # choice, which is the one we want to test - the second
    #
    os.environ['GCALCLI_TEST_CYCLE'] = "0"
    # set opts so we send current to stdout
    default_options.update(
        [("text", "Test event"), ("details", {"description": True})]
    )
    # we need to choose 'd' from edit menu
    monkeypatch.setattr(gcalcli.gcalcli, "edit_choice_input",
                        lambda: "d")
    # we set a new description at the prompt
    monkeypatch.setattr(gcalcli.validators, "validate_input",
                        lambda _useless: "Added Desc")
    gcal = PatchedGCalIForEvents(**(default_options))
    gcal.ModifyEvents(gcal._edit_event, default_options)
    captured = capsys.readouterr()
    os.environ.pop('GCALCLI_TEST_CYCLE')
    assert "Added Desc" in captured.out


def test_remove_event_description(capsys, monkeypatch,
                                  PatchedGCalIForEvents, default_options):
    # we need a func to pass into gcalcli.validators.validate_input
    def _useless():
        pass
    # we need a way to be able to jump out of the edit loop
    # set an env variable here, then change it after the first
    # choice, which is the one we want to test - the second
    #
    os.environ['GCALCLI_TEST_CYCLE'] = "0"
    # set opts so we send current to stdout
    default_options.update(
        [("text", "Test event"), ("details", {"description": True})]
    )
    # we need to choose 'd' from edit menu
    monkeypatch.setattr(gcalcli.gcalcli, "edit_choice_input",
                        lambda: "d")
    # we use a '.' at the prompt to remove the current value
    monkeypatch.setattr(gcalcli.validators, "validate_input",
                        lambda _useless: ".")
    gcal = PatchedGCalIForEvents(**(default_options))
    gcal.ModifyEvents(gcal._edit_event, default_options)
    captured = capsys.readouterr()
    os.environ.pop('GCALCLI_TEST_CYCLE')
    assert "TEST DESCRIPTION" not in captured.out


def test_edit_event_location(capsys, monkeypatch,
                             PatchedGCalIForEvents, default_options):
    # we need a func to pass into gcalcli.validators.validate_input
    def _useless():
        pass
    # we need a way to be able to jump out of the edit loop
    # set an env variable here, then change it after the first
    # choice, which is the one we want to test - the second
    #
    os.environ['GCALCLI_TEST_CYCLE'] = "0"
    # set opts so we send current to stdout
    default_options.update(
        [("text", "Test event"),
         ("details", {"description": True, "location": True, "width": 80})
         ])
    # we need to choose 'l' from edit menu
    monkeypatch.setattr(gcalcli.gcalcli, "edit_choice_input",
                        lambda: "l")
    # we set a new location at the prompt
    monkeypatch.setattr(gcalcli.validators, "validate_input",
                        lambda _useless: "New Location")
    gcal = PatchedGCalIForEvents(**(default_options))
    gcal.ModifyEvents(gcal._edit_event, default_options)
    captured = capsys.readouterr()
    os.environ.pop('GCALCLI_TEST_CYCLE')
    assert "New Location" in captured.out


def test_remove_event_location(capsys, monkeypatch,
                               PatchedGCalIForEvents, default_options):
    # we need a func to pass into gcalcli.validators.validate_input
    def _useless():
        pass
    # we need a way to be able to jump out of the edit loop
    # set an env variable here, then change it after the first
    # choice, which is the one we want to test - the second
    #
    os.environ['GCALCLI_TEST_CYCLE'] = "0"
    # set opts so we send current to stdout
    default_options.update(
        [("text", "Test event"),
         ("details", {"description": True, "location": True, "width": 80})
         ])
    # we need to choose 'l' from edit menu
    monkeypatch.setattr(gcalcli.gcalcli, "edit_choice_input",
                        lambda: "l")
    # we use a '.' at the prompt to remove the current value
    monkeypatch.setattr(gcalcli.validators, "validate_input",
                        lambda _useless: ".")
    gcal = PatchedGCalIForEvents(**(default_options))
    gcal.ModifyEvents(gcal._edit_event, default_options)
    captured = capsys.readouterr()
    os.environ.pop('GCALCLI_TEST_CYCLE')
    assert "Neverwhere" not in captured.out
