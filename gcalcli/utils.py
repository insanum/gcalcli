import calendar
import time
import locale
import six
import re
from dateutil.tz import tzlocal
from dateutil.parser import parse as dateutil_parse
from datetime import datetime, timedelta
from parsedatetime.parsedatetime import Calendar


locale.setlocale(locale.LC_ALL, '')
fuzzy_date_parse = Calendar().parse

REMINDER_REGEX = r'^(\d+)([wdhm]?)(?:\s+(popup|email|sms))?$'


def parse_reminder(rem):
    match = re.match(REMINDER_REGEX, rem)
    if not match:
        # Allow argparse to generate a message when parsing options
        return None
    n = int(match.group(1))
    t = match.group(2)
    m = match.group(3)
    if t == 'w':
        n = n * 7 * 24 * 60
    elif t == 'd':
        n = n * 24 * 60
    elif t == 'h':
        n = n * 60

    if not m:
        m = 'popup'

    return n, m


def set_locale(new_locale):
    try:
        locale.setlocale(locale.LC_ALL, new_locale)
    except locale.Error as exc:
        raise ValueError(
                'Error: ' + str(exc) +
                '!\n Check supported locales of your system.\n')


def _u(text):
    encoding = locale.getlocale()[1] or \
            locale.getpreferredencoding(False) or 'UTF-8'
    if issubclass(type(text), six.text_type):
        return text
    if not issubclass(type(text), six.string_types):
        if six.PY3:
            if isinstance(text, bytes):
                return six.text_type(text, encoding, 'replace')
            else:
                return six.text_type(text)
        elif hasattr(text, '__unicode__'):
            return six.text_type(text)
        else:
            return six.text_type(bytes(text), encoding, 'replace')
    else:
        return text.decode(encoding, 'replace')


def get_times_from_duration(when, duration=0, allday=False):

    try:
        start = get_time_from_str(when)
    except Exception:
        raise ValueError('Date and time is invalid: %s\n' % (when))

    if allday:
        try:
            stop = start + timedelta(days=float(duration))
        except Exception:
            raise ValueError(
                    'Duration time (days) is invalid: %s\n' % (duration))

        start = start.date().isoformat()
        stop = stop.date().isoformat()

    else:
        try:
            stop = start + timedelta(minutes=float(duration))
        except Exception:
            raise ValueError(
                    'Duration time (minutes) is invalid: %s\n' % (duration))

        start = start.isoformat()
        stop = stop.isoformat()

    return start, stop


def get_time_from_str(when):
    """Convert a string to a time: first uses the dateutil parser, falls back
    on fuzzy matching with parsedatetime
    """
    zero_oclock_today = datetime.now(tzlocal()).replace(
            hour=0, minute=0, second=0, microsecond=0)

    try:
        event_time = dateutil_parse(when, default=zero_oclock_today)
    except ValueError:
        struct, result = fuzzy_date_parse(when)
        if not result:
            raise ValueError('Date and time is invalid: %s' % (when))
        event_time = datetime.fromtimestamp(time.mktime(struct), tzlocal())

    return event_time


def days_since_epoch(dt):
    __DAYS_IN_SECONDS__ = 24 * 60 * 60
    return calendar.timegm(dt.timetuple()) / __DAYS_IN_SECONDS__
