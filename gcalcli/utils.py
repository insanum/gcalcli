import calendar
import time
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


def get_time_from_str(when, duration=0, allday=False):
    dtp = DateTimeParser()

    try:
        start = dtp.fromString(when)
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


def days_since_epoch(dt):
    __DAYS_IN_SECONDS__ = 24 * 60 * 60
    return calendar.timegm(dt.timetuple()) / __DAYS_IN_SECONDS__


class DateTimeParser:
    def __init__(self):
        self.pdtCalendar = parsedatetime.Calendar()

    def fromString(self, eWhen):
        defaultDateTime = datetime.now(tzlocal()).replace(hour=0,
                                                          minute=0,
                                                          second=0,
                                                          microsecond=0)

        try:
            eTimeStart = parse(eWhen, default=defaultDateTime)
        except Exception:
            struct, result = self.pdtCalendar.parse(eWhen)
            if not result:
                raise ValueError("Date and time is invalid")
            eTimeStart = datetime.fromtimestamp(time.mktime(struct), tzlocal())

        return eTimeStart
