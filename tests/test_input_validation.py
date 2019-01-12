import pytest

from gcalcli.validators import validate_input, ValidationError
from gcalcli.validators import STR_NOT_EMPTY, PARSABLE_DATE

import gcalcli.validators

# Tests required:
#
# * Title: any string, not blank
# * Location: any string, not blank
# * When: string that can be parsed by dateutil
# * Duration: string that can be cast to int
# * Description: any string, not blank
# * Color: any string matching: blueberry, lavendar, grape, etc
# * Reminder: a valid reminder


def test_any_string_not_blank_validator(monkeypatch):
    # Empty string
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "")
    with pytest.raises(ValidationError):
        validate_input(STR_NOT_EMPTY) == ValidationError(
            "Input here cannot be empty")

    # None
    monkeypatch.setattr(gcalcli.validators, "input", lambda: None)
    with pytest.raises(ValidationError):
        validate_input(STR_NOT_EMPTY) == ValidationError(
            "Input here cannot be empty")

    # Valid string
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "Valid Text")
    assert validate_input(STR_NOT_EMPTY) == "Valid Text"


def test_any_string_parsable_by_dateutil(monkeypatch):
    # non-date raises ValidationError
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "NON-DATE STR")
    with pytest.raises(ValidationError):
        validate_input(PARSABLE_DATE) == ValidationError(
            "Must be a date (e.g. 2019-01-01, 2nd Jan, Jan 4th, etc)"
        )
    # date string
    monkeypatch.setattr(gcalcli.validators, "input", lambda: "2nd January")
    validate_input(PARSABLE_DATE) == "2nd January"
