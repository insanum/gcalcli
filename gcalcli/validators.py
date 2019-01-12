from datetime import date
from builtins import input

from dateutil.parser import parse


class ValidationError(Exception):
    pass


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
            "Must be a date (e.g. 2019-01-01, 2nd Jan, Jan 4th, etc)")


def non_blank_str_validator(input_str):
    """
    A simple filter allowing string len > 1 and not None
    Raises ValidatorError otherwise.
    """
    if input_str in [None, ""]:
        raise ValidationError("Input here cannot be empty")
    else:
        return input_str


def validate_input(validator_func):
    """
    Wrapper around Validator funcs.
    """
    inp_str = input()
    return validator_func(inp_str)


STR_NOT_EMPTY = non_blank_str_validator
PARSABLE_DATE = parsable_date_validator
