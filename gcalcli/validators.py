from __future__ import absolute_import

import re

from six.moves import input

from gcalcli.utils import valid_override_colors, REMINDER_REGEX
from gcalcli.exceptions import ValidationError

from dateutil.parser import parse


def get_input(printer, prompt, validator_func):
    printer.msg(prompt, 'magenta')
    while True:
        try:
            output = validate_input(validator_func)
            return output
        except ValidationError as e:
            printer.msg(e.message, "red")
            printer.msg(prompt, 'magenta')


def valid_colors_validator(input_str):
    """
    A filter allowing only the following strings:
        * basil
        * banana
        * tomato
        * lavender
        * flamingo
        * blueberry
        * peacock
        * grape
    Raises ValidationError otherwise.
    """
    valid_override_colors.append("")  # allow empty
    try:
        assert input_str in valid_override_colors
        return input_str
    except AssertionError:
        raise ValidationError("Expected colors are: basil, peacock, grape, "
                              "lavender, blueberry, tomato, flamingo or "
                              "banana. (Ctrl-C to exit)\n")


def str_to_int_validator(input_str):
    """
    A filter allowing any string which can be
    converted to an int.
    Raises ValidationError otherwise.
    """
    try:
        int(input_str)
        return input_str
    except ValueError:
        raise ValidationError(
            "Input here must be a number. (Ctrl-C to exit)\n"
        )


def parsable_date_validator(input_str):
    """
    A filter allowing any string which can be parsed
    by dateutil.
    Raises ValidationError otherwise.
    """
    try:
        parse(input_str)
        return input_str
    except ValueError:
        raise ValidationError(
            "Expected format: a date (e.g. 2019-01-01, 2nd Jan, Jan 4th, etc)"
            " or valid time if today. (Ctrl-C to exit)\n"
        )


def str_allow_empty_validator(input_str):
    """
    A simple filter that allows any string to pass.
    Included for completeness and for future validation if required.
    """
    return input_str


def non_blank_str_validator(input_str):
    """
    A simple filter allowing string len > 1 and not None
    Raises ValidationError otherwise.
    """
    if input_str in [None, ""]:
        raise ValidationError(
            "Input here cannot be empty. (Ctrl-C to exit)\n"
        )
    else:
        return input_str


def valid_reminder_validator(input_str):
    """
    Allows a string that matches utils.REMINDER_REGEX.
    Raises ValidationError otherwise.
    """
    match = re.match(REMINDER_REGEX, input_str)
    if match or input_str == ".":
        return input_str
    else:
        raise ValidationError("Expected format: <number><w|d|h|m> "
                              "<popup|email|sms>. (Ctrl-C to exit)\n")


def validate_input(validator_func):
    """
    Wrapper around Validator funcs.
    """
    inp_str = input()
    return validator_func(inp_str)


STR_NOT_EMPTY = non_blank_str_validator
STR_ALLOW_EMPTY = str_allow_empty_validator
STR_TO_INT = str_to_int_validator
PARSABLE_DATE = parsable_date_validator
VALID_COLORS = valid_colors_validator
REMINDER = valid_reminder_validator
