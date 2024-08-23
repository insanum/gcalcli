class GcalcliError(Exception):
    pass


class ValidationError(Exception):
    def __init__(self, message):
        super(ValidationError, self).__init__(message)
        self.message = message


class ReadonlyError(Exception):
    def __init__(self, fieldname, message):
        message = 'Field {} is read-only. {}'.format(fieldname, message)
        super(ReadonlyError, self).__init__(message)


class ReadonlyCheckError(ReadonlyError):
    _fmt = 'Current value "{}" does not match update value "{}"'

    def __init__(self, fieldname, curr_value, mod_value):
        message = self._fmt.format(curr_value, mod_value)
        super(ReadonlyCheckError, self).__init__(fieldname, message)


def raise_one_cal_error(cals):
    raise GcalcliError(
        'You must only specify a single calendar\n'
        'Calendars: {}\n'.format(cals)
    )
