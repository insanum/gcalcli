import pytest

from gcalcli.validators import validate_input, ValidationError
from gcalcli.validators import (STR_NOT_EMPTY,
                                PARSABLE_DATE,
                                PARSABLE_DURATION,
                                STR_TO_INT,
                                STR_ALLOW_EMPTY,
                                REMINDER,
                                VALID_COLORS)
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
    monkeypatch.setattr("builtins.input", lambda: "")
    with pytest.raises(ValidationError):
        validate_input(STR_NOT_EMPTY) == ValidationError(
            "Input here cannot be empty")

    # None raises ValidationError
    monkeypatch.setattr("builtins.input", lambda: None)
    with pytest.raises(ValidationError):
        validate_input(STR_NOT_EMPTY) == ValidationError(
            "Input here cannot be empty")

    # Valid string passes
    monkeypatch.setattr("builtins.input", lambda: "Valid Text")
    assert validate_input(STR_NOT_EMPTY) == "Valid Text"


def test_any_string_parsable_by_dateutil(monkeypatch):
    # non-date raises ValidationError
    monkeypatch.setattr("builtins.input", lambda: "NON-DATE STR")
    with pytest.raises(ValidationError):
        validate_input(PARSABLE_DATE) == ValidationError(
            "Expected format: a date (e.g. 2019-01-01, tomorrow 10am, "
            "2nd Jan, Jan 4th, etc) or valid time if today. "
            "(Ctrl-C to exit)\n"
        )

    # date string passes
    monkeypatch.setattr("builtins.input", lambda: "2nd January")
    validate_input(PARSABLE_DATE) == "2nd January"


def test_any_string_parsable_by_parsedatetime(monkeypatch):
    # non-date raises ValidationError
    monkeypatch.setattr("builtins.input", lambda: "NON-DATE STR")
    with pytest.raises(ValidationError) as ve:
        validate_input(PARSABLE_DURATION)
    assert ve.value.message == (
            'Expected format: a duration (e.g. 1m, 1s, 1h3m)'
            '(Ctrl-C to exit)\n'
        )

    # duration string passes
    monkeypatch.setattr("builtins.input", lambda: "1m")
    assert validate_input(PARSABLE_DURATION) == "1m"

    # duration string passes
    monkeypatch.setattr("builtins.input", lambda: "1h2m")
    assert validate_input(PARSABLE_DURATION) == "1h2m"


def test_string_can_be_cast_to_int(monkeypatch):
    # non int-castable string raises ValidationError
    monkeypatch.setattr("builtins.input", lambda: "X")
    with pytest.raises(ValidationError):
        validate_input(STR_TO_INT) == ValidationError(
            "Input here must be a number")

    # int string passes
    monkeypatch.setattr("builtins.input", lambda: "10")
    validate_input(STR_TO_INT) == "10"


def test_for_valid_colour_name(monkeypatch):
    # non valid colour raises ValidationError
    monkeypatch.setattr("builtins.input", lambda: "purple")
    with pytest.raises(ValidationError):
        validate_input(VALID_COLORS) == ValidationError(
            "purple is not a valid color value to use here. Please "
            "use one of basil, peacock, grape, lavender, blueberry,"
            "tomato, safe, flamingo or banana."
        )
    # valid colour passes
    monkeypatch.setattr("builtins.input", lambda: "grape")
    validate_input(VALID_COLORS) == "grape"

    # empty str passes
    monkeypatch.setattr("builtins.input", lambda: "")
    validate_input(VALID_COLORS) == ""


def test_any_string_and_blank(monkeypatch):
    # string passes
    monkeypatch.setattr("builtins.input", lambda: "TEST")
    validate_input(STR_ALLOW_EMPTY) == "TEST"


def test_reminder(monkeypatch):
    # valid reminders pass
    monkeypatch.setattr("builtins.input", lambda: "10m email")
    validate_input(REMINDER) == "10m email"

    monkeypatch.setattr("builtins.input", lambda: "10 popup")
    validate_input(REMINDER) == "10m email"

    monkeypatch.setattr("builtins.input", lambda: "10m sms")
    validate_input(REMINDER) == "10m email"

    monkeypatch.setattr("builtins.input", lambda: "12323")
    validate_input(REMINDER) == "10m email"

    # invalid reminder raises ValidationError
    monkeypatch.setattr("builtins.input", lambda: "meaningless")
    with pytest.raises(ValidationError):
        validate_input(REMINDER) == ValidationError(
            "Format: <number><w|d|h|m> <popup|email|sms>\n")

    # invalid reminder raises ValidationError
    monkeypatch.setattr("builtins.input", lambda: "")
    with pytest.raises(ValidationError):
        validate_input(REMINDER) == ValidationError(
            "Format: <number><w|d|h|m> <popup|email|sms>\n")
