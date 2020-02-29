import re

from gcalcli.exceptions import ValidationError
from gcalcli.utils import (REMINDER_REGEX, get_time_from_str,
                           get_timedelta_from_str)

# TODO: in the future, pull these from the API
# https://developers.google.com/calendar/v3/reference/colors
VALID_OVERRIDE_COLORS = ['lavender', 'sage', 'grape', 'flamingo',
                         'banana', 'tangerine', 'peacock', 'graphite',
                         'blueberry', 'basil', 'tomato']


def get_override_color_id(color):
    return str(VALID_OVERRIDE_COLORS.index(color) + 1)


def get_input(printer, prompt, validator_func):
    printer.msg(prompt, 'magenta')
    while True:
        try:
            output = validate_input(validator_func)
            return output
        except ValidationError as e:
            printer.msg(e.message, 'red')
            printer.msg(prompt, 'magenta')


def color_validator(input_str):
    """
    A filter allowing only the particular colors used by the Google Calendar
    API

    Raises ValidationError otherwise.
    """
    try:
        assert input_str in VALID_OVERRIDE_COLORS + ['']
        return input_str
    except AssertionError:
        raise ValidationError(
                'Expected colors are: ' +
                ', '.join(color for color in VALID_OVERRIDE_COLORS) +
                '. (Ctrl-C to exit)\n')


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
            'Input here must be a number. (Ctrl-C to exit)\n'
        )


def parsable_date_validator(input_str):
    """
    A filter allowing any string which can be parsed
    by dateutil.
    Raises ValidationError otherwise.
    """
    try:
        get_time_from_str(input_str)
        return input_str
    except ValueError:
        raise ValidationError(
            'Expected format: a date (e.g. 2019-01-01, tomorrow 10am, '
            '2nd Jan, Jan 4th, etc) or valid time if today. '
            '(Ctrl-C to exit)\n'
        )


def parsable_duration_validator(input_str):
    """
    A filter allowing any duration string which can be parsed
    by parsedatetime.
    Raises ValidationError otherwise.
    """
    try:
        get_timedelta_from_str(input_str)
        return input_str
    except ValueError:
        raise ValidationError(
            'Expected format: a duration (e.g. 1m, 1s, 1h3m)'
            '(Ctrl-C to exit)\n'
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
    if input_str in [None, '']:
        raise ValidationError(
            'Input here cannot be empty. (Ctrl-C to exit)\n'
        )
    else:
        return input_str


def reminder_validator(input_str):
    """
    Allows a string that matches utils.REMINDER_REGEX.
    Raises ValidationError otherwise.
    """
    match = re.match(REMINDER_REGEX, input_str)
    if match or input_str == '.':
        return input_str
    else:
        raise ValidationError('Expected format: <number><w|d|h|m> '
                              '<popup|email|sms>. (Ctrl-C to exit)\n')


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
PARSABLE_DURATION = parsable_duration_validator
VALID_COLORS = color_validator
REMINDER = reminder_validator
