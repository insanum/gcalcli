import pytest

from gcalcli.validators import validate_input, ValidationError
from gcalcli.validators import (STR_NOT_EMPTY,
                                PARSABLE_DATE,
                                PARSABLE_DURATION,
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
    with pytest.raises(ValidationError) as ve:
        validate_input(STR_NOT_EMPTY)
    assert ve.value.message == ("Input here cannot be empty. "
                                "(Ctrl-C to exit)\n")

    # None raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: None)
    with pytest.raises(ValidationError) as ve:
        validate_input(STR_NOT_EMPTY)
    assert ve.value.message == ("Input here cannot be empty. "
                                "(Ctrl-C to exit)\n")

    # Valid string passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "Valid Text")
    assert validate_input(STR_NOT_EMPTY) == "Valid Text"


def test_any_string_parsable_by_dateutil(monkeypatch):
    # non-date raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "NON-DATE STR")
    with pytest.raises(ValidationError) as ve:
        validate_input(PARSABLE_DATE)
    assert ve.value.message == (
            "Expected format: a date (e.g. 2019-01-01, tomorrow 10am, "
            "2nd Jan, Jan 4th, etc) or valid time if today. "
            "(Ctrl-C to exit)\n"
        )

    # date string passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "2nd January")
    assert validate_input(PARSABLE_DATE) == "2nd January"


def test_any_string_parsable_by_parsedatetime(monkeypatch):
    # non-date raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "NON-DATE STR")
    with pytest.raises(ValidationError) as ve:
        validate_input(PARSABLE_DURATION)
    assert ve.value.message == (
            'Expected format: a duration (e.g. 1m, 1s, 1h3m)'
            '(Ctrl-C to exit)\n'
        )

    # duration string passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "1m")
    assert validate_input(PARSABLE_DURATION) == "1m"

    # duration string passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "1h2m")
    assert validate_input(PARSABLE_DURATION) == "1h2m"


def test_string_can_be_cast_to_int(monkeypatch):
    # non int-castable string raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "X")
    with pytest.raises(ValidationError) as ve:
        validate_input(STR_TO_INT)
    assert ve.value.message == ("Input here must be a number. "
                                "(Ctrl-C to exit)\n")

    # int string passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "10")
    assert validate_input(STR_TO_INT) == "10"


def test_for_valid_colour_name(monkeypatch):
    # non valid colour raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "purple")
    with pytest.raises(ValidationError) as ve:
        validate_input(VALID_COLORS)

    assert ve.value.message == (
        "Expected colors are: lavender, sage, grape, flamingo, banana, "
        "tangerine, peacock, graphite, blueberry, basil, tomato. "
        "(Ctrl-C to exit)\n"
    )

    # valid colour passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "grape")
    assert validate_input(VALID_COLORS) == "grape"

    # empty str passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "")
    assert validate_input(VALID_COLORS) == ""


def test_any_string_and_blank(monkeypatch):
    # string passes
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "TEST")
    assert validate_input(STR_ALLOW_EMPTY) == "TEST"


def test_reminder(monkeypatch):
    # valid reminders pass
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "10m email")
    assert validate_input(REMINDER) == "10m email"

    monkeypatch.setattr(gcalcli.validators, "input", lambda: "10 popup")
    assert validate_input(REMINDER) == "10 popup"

    monkeypatch.setattr(gcalcli.validators, "input", lambda: "10m sms")
    assert validate_input(REMINDER) == "10m sms"

    monkeypatch.setattr(gcalcli.validators, "input", lambda: "12323")
    assert validate_input(REMINDER) == "12323"

    # invalid reminder raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "meaningless")
    with pytest.raises(ValidationError) as ve:
        validate_input(REMINDER)
    assert ve.value.message == ('Expected format: <number><w|d|h|m> '
                                '<popup|email|sms>. (Ctrl-C to exit)\n')

    # invalid reminder raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "")
    with pytest.raises(ValidationError) as ve:
        validate_input(REMINDER)

    assert ve.value.message == ('Expected format: <number><w|d|h|m> '
                                '<popup|email|sms>. (Ctrl-C to exit)\n')
