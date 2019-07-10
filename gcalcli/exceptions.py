class GcalcliError(Exception):
    pass


class ValidationError(Exception):
    def __init__(self, message):
        super(ValidationError, self).__init__(message)
        self.message = message


def raise_one_cal_error(cals):
    raise GcalcliError(
        'You must only specify a single calendar\n'
        'Calendars: {}\n'.format(cals)
    )
