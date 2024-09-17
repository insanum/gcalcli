import pytest

from gcalcli.validators import (PARSABLE_DATE, PARSABLE_DURATION, REMINDER,
                                STR_ALLOW_EMPTY, STR_NOT_EMPTY, STR_TO_INT,
                                VALID_COLORS, ValidationError)

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
        STR_NOT_EMPTY(input()) == ValidationError(
            "Input here cannot be empty")

    # None raises ValidationError
    monkeypatch.setattr("builtins.input", lambda: None)
    with pytest.raises(ValidationError):
        STR_NOT_EMPTY(input()) == ValidationError(
            "Input here cannot be empty")

    # Valid string passes
    monkeypatch.setattr("builtins.input", lambda: "Valid Text")
    assert STR_NOT_EMPTY(input()) == "Valid Text"


def test_any_string_parsable_by_dateutil(monkeypatch):
    # non-date raises ValidationError
    monkeypatch.setattr("builtins.input", lambda: "NON-DATE STR")
    with pytest.raises(ValidationError):
        PARSABLE_DATE(input()) == ValidationError(
            "Expected format: a date (e.g. 2019-01-01, tomorrow 10am, "
            "2nd Jan, Jan 4th, etc) or valid time if today. "
            "(Ctrl-C to exit)\n"
        )

    # date string passes
    monkeypatch.setattr("builtins.input", lambda: "2nd January")
    PARSABLE_DATE(input()) == "2nd January"


def test_any_string_parsable_by_parsedatetime(monkeypatch):
    # non-date raises ValidationError
    monkeypatch.setattr("builtins.input", lambda: "NON-DATE STR")
    with pytest.raises(ValidationError) as ve:
        PARSABLE_DURATION(input())
    assert ve.value.message == (
            'Expected format: a duration (e.g. 1m, 1s, 1h3m)'
            '(Ctrl-C to exit)\n'
        )

    # duration string passes
    monkeypatch.setattr("builtins.input", lambda: "1m")
    assert PARSABLE_DURATION(input()) == "1m"

    # duration string passes
    monkeypatch.setattr("builtins.input", lambda: "1h2m")
    assert PARSABLE_DURATION(input()) == "1h2m"


def test_string_can_be_cast_to_int(monkeypatch):
    # non int-castable string raises ValidationError
    monkeypatch.setattr("builtins.input", lambda: "X")
    with pytest.raises(ValidationError):
        STR_TO_INT(input()) == ValidationError(
            "Input here must be a number")

    # int string passes
    monkeypatch.setattr("builtins.input", lambda: "10")
    STR_TO_INT(input()) == "10"


def test_for_valid_colour_name(monkeypatch):
    # non valid colour raises ValidationError
    monkeypatch.setattr("builtins.input", lambda: "purple")
    with pytest.raises(ValidationError):
        VALID_COLORS(input()) == ValidationError(
            "purple is not a valid color value to use here. Please "
            "use one of basil, peacock, grape, lavender, blueberry,"
            "tomato, safe, flamingo or banana."
        )
    # valid colour passes
    monkeypatch.setattr("builtins.input", lambda: "grape")
    VALID_COLORS(input()) == "grape"

    # empty str passes
    monkeypatch.setattr("builtins.input", lambda: "")
    VALID_COLORS(input()) == ""


def test_any_string_and_blank(monkeypatch):
    # string passes
    monkeypatch.setattr("builtins.input", lambda: "TEST")
    STR_ALLOW_EMPTY(input()) == "TEST"


def test_reminder(monkeypatch):
    # valid reminders pass
    monkeypatch.setattr("builtins.input", lambda: "10m email")
    REMINDER(input()) == "10m email"

    monkeypatch.setattr("builtins.input", lambda: "10 popup")
    REMINDER(input()) == "10m email"

    monkeypatch.setattr("builtins.input", lambda: "10m sms")
    REMINDER(input()) == "10m email"

    monkeypatch.setattr("builtins.input", lambda: "12323")
    REMINDER(input()) == "10m email"

    # invalid reminder raises ValidationError
    monkeypatch.setattr("builtins.input", lambda: "meaningless")
    with pytest.raises(ValidationError):
        REMINDER(input()) == ValidationError(
            "Format: <number><w|d|h|m> <popup|email|sms>\n")

    # invalid reminder raises ValidationError
    monkeypatch.setattr("builtins.input", lambda: "")
    with pytest.raises(ValidationError):
        REMINDER(input()) == ValidationError(
            "Format: <number><w|d|h|m> <popup|email|sms>\n")
