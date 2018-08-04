import calendar
import time
import locale
import six
from dateutil.tz import tzlocal
from dateutil.parser import parse
from datetime import datetime, timedelta
# If they have parsedatetime, we'll use it for fuzzy datetime comparison.  If
# not, we just return a fake failure every time and use only dateutil.
try:
    from parsedatetime import parsedatetime
except ImportError:
    class parsedatetime:
        class Calendar:
            def parse(self, string):
                return ([], 0)

locale.setlocale(locale.LC_ALL, '')
parse_date_time_calendar = parsedatetime.Calendar()


def set_locale(new_locale):
    try:
        locale.setlocale(locale.LC_ALL, new_locale)
    except locale.Error as exc:
        raise ValueError(
                'Error: ' + str(exc) +
                '!\n Check supported locales of your system.\n')


def _u(text):
    encoding = locale.getlocale()[1] or \
            locale.getpreferredencoding(False) or "UTF-8"
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
        raise ValueError('Date and time is invalid!\n')

    if allday:
        try:
            stop = start + timedelta(days=float(duration))
        except Exception:
            raise ValueError('Duration time (days) is invalid\n')

        start = start.date().isoformat()
        stop = stop.date().isoformat()

    else:
        try:
            stop = start + timedelta(minutes=float(duration))
        except Exception:
            raise ValueError('Duration time (minutes) is invalid\n')

        start = start.isoformat()
        stop = stop.isoformat()

    return start, stop


def get_time_from_str(when):
    defaultDateTime = datetime.now(tzlocal()).replace(hour=0,
                                                      minute=0,
                                                      second=0,
                                                      microsecond=0)

    try:
        event_time = parse(when, default=defaultDateTime)
    except Exception:
        struct, result = parse_date_time_calendar.parse(when)
        if not result:
            raise ValueError("Date and time is invalid")
        event_time = datetime.fromtimestamp(time.mktime(struct), tzlocal())

    return event_time


def days_since_epoch(dt):
    __DAYS_IN_SECONDS__ = 24 * 60 * 60
    return calendar.timegm(dt.timetuple()) / __DAYS_IN_SECONDS__
