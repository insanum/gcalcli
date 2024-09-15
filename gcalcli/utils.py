import calendar
import locale
import os
import pathlib
import re
import subprocess
import time
from datetime import datetime, timedelta
from typing import Tuple

from dateutil.parser import parse as dateutil_parse
from dateutil.tz import tzlocal
from parsedatetime.parsedatetime import Calendar

locale.setlocale(locale.LC_ALL, '')
fuzzy_date_parse = Calendar().parse
fuzzy_datetime_parse = Calendar().parseDT


REMINDER_REGEX = r'^(\d+)([wdhm]?)(?:\s+(popup|email|sms))?$'

DURATION_REGEX = re.compile(
                r'^((?P<days>[\.\d]+?)(?:d|day|days))?[ :]*'
                r'((?P<hours>[\.\d]+?)(?:h|hour|hours))?[ :]*'
                r'((?P<minutes>[\.\d]+?)(?:m|min|mins|minute|minutes))?[ :]*'
                r'((?P<seconds>[\.\d]+?)(?:s|sec|secs|second|seconds))?$'
                )


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


def get_times_from_duration(
    when, duration=0, end=None, allday=False
) -> Tuple[str, str]:
    try:
        start = get_time_from_str(when)
    except Exception:
        raise ValueError('Date and time is invalid: %s\n' % (when))

    if end is not None:
        stop = get_time_from_str(end)
    elif allday:
        try:
            stop = start + timedelta(days=float(duration))
        except Exception:
            raise ValueError(
                'Duration time (days) is invalid: %s\n' % (duration)
            )
        start = start.date()
        stop = stop.date()
    else:
        try:
            stop = start + get_timedelta_from_str(duration)
        except Exception:
            raise ValueError('Duration time is invalid: %s\n' % (duration))

    return start.isoformat(), stop.isoformat()


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


def get_timedelta_from_str(delta):
    """
    Parse a time string a timedelta object.
    Formats:
      - number -> duration in minutes
      - "1:10" -> hour and minutes
      - "1d 1h 1m" -> days, hours, minutes
    Based on https://stackoverflow.com/a/51916936/12880
    """
    parsed_delta = None
    try:
        parsed_delta = timedelta(minutes=float(delta))
    except ValueError:
        pass
    if parsed_delta is None:
        parts = DURATION_REGEX.match(delta)
        if parts is not None:
            try:
                time_params = {name: float(param)
                               for name, param
                               in parts.groupdict().items() if param}
                parsed_delta = timedelta(**time_params)
            except ValueError:
                pass
    if parsed_delta is None:
        dt, result = fuzzy_datetime_parse(delta, sourceTime=datetime.min)
        if result:
            parsed_delta = dt - datetime.min
    if parsed_delta is None:
        raise ValueError('Duration is invalid: %s' % (delta))
    return parsed_delta


def days_since_epoch(dt):
    __DAYS_IN_SECONDS__ = 24 * 60 * 60
    return calendar.timegm(dt.timetuple()) / __DAYS_IN_SECONDS__


def agenda_time_fmt(dt, military):
    hour_min_fmt = '%H:%M' if military else '%I:%M'
    ampm = '' if military else dt.strftime('%p').lower()
    return dt.strftime(hour_min_fmt).lstrip('0') + ampm


def is_all_day(event):
    # XXX: currently gcalcli represents all-day events as those that both begin
    # and end at midnight. This is ambiguous with Google Calendar events that
    # are not all-day but happen to begin and end at midnight.

    return (event['s'].hour == 0 and event['s'].minute == 0
            and event['e'].hour == 0 and event['e'].minute == 0)

def localize_datetime(dt):
    if not hasattr(dt, 'tzinfo'):  # Why are we skipping these?
        return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tzlocal())
    else:
        return dt.astimezone(tzlocal())


def launch_editor(path: str | os.PathLike):
    if hasattr(os, 'startfile'):
        os.startfile(path, 'edit')
        return
    for editor in (
        'editor',
        os.environ.get('EDITOR', None),
        'xdg-open',
        'open',
    ):
        if not editor:
            continue
        try:
            subprocess.call((editor, path))
            return
        except OSError:
            pass
    raise OSError(f'No editor/launcher detected on your system to edit {path}')


def shorten_path(path: pathlib.Path) -> pathlib.Path:
    """Try to shorten path using special characters like ~.

    Returns original path unmodified if it can't be shortened.
    """
    tilde_home = pathlib.Path('~')
    expanduser_len = len(tilde_home.expanduser().parts)
    if path.parts[:expanduser_len] == tilde_home.expanduser().parts:
        return tilde_home.joinpath(*path.parts[expanduser_len:])
    return path
