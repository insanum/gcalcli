"""Handlers for specific details of events."""

from collections import OrderedDict
from datetime import datetime
from itertools import chain

from dateutil.parser import isoparse, parse

from .exceptions import ReadonlyCheckError, ReadonlyError
from .utils import is_all_day

FMT_DATE = '%Y-%m-%d'
FMT_TIME = '%H:%M'
TODAY = datetime.now().date()
ACTION_DEFAULT = 'patch'

URL_PROPS = OrderedDict([('html_link', 'htmlLink'),
                         ('hangout_link', 'hangoutLink')])
ENTRY_POINT_PROPS = OrderedDict([('conference_entry_point_type',
                                  'entryPointType'),
                                 ('conference_uri', 'uri')])


def _valid_title(event):
    if 'summary' in event and event['summary'].strip():
        return event['summary']
    else:
        return '(No title)'


class Handler:
    """Handler for a specific detail of an event."""

    # list of strings for fieldnames provided by this object
    fieldnames: list[str] = []

    @classmethod
    def get(cls, event):
        """Return simple string representation for columnar output."""
        raise NotImplementedError

    @classmethod
    def patch(cls, cal, event, fieldname, value):
        """Patch event from value."""
        raise NotImplementedError


class SingleFieldHandler(Handler):
    """Handler for a detail that only produces one column."""

    @classmethod
    def get(cls, event):
        return [cls._get(event).strip()]

    @classmethod
    def patch(cls, cal, event, fieldname, value):
        return cls._patch(event, value)


class SimpleSingleFieldHandler(SingleFieldHandler):
    """Handler for single-string details that require no special processing."""

    @classmethod
    def _get(cls, event):
        return event.get(cls.fieldnames[0], '')

    @classmethod
    def _patch(cls, event, value):
        event[cls.fieldnames[0]] = value


class Time(Handler):
    """Handler for dates and times."""

    fieldnames = ['start_date', 'start_time', 'end_date', 'end_time']

    @classmethod
    def _datetime_to_fields(cls, instant, all_day):
        instant_date = instant.strftime(FMT_DATE)

        if all_day:
            instant_time = ''
        else:
            instant_time = instant.strftime(FMT_TIME)

        return [instant_date, instant_time]

    @classmethod
    def get(cls, event):
        all_day = is_all_day(event)

        start_fields = cls._datetime_to_fields(event['s'], all_day)
        end_fields = cls._datetime_to_fields(event['e'], all_day)

        return start_fields + end_fields

    @classmethod
    def patch(cls, cal, event, fieldname, value):
        instant_name, _, unit = fieldname.partition('_')

        assert instant_name in {'start', 'end'}

        if unit == 'date':
            instant = event[instant_name] = {}
            instant_date = parse(value, default=TODAY)

            instant['date'] = instant_date.isoformat()
            instant['dateTime'] = None  # clear any previous non-all-day time
        else:
            assert unit == 'time'

            # If the time field is empty, do nothing.
            # This enables all day events.
            if not value.strip():
                return

            # date must be an earlier TSV field than time
            instant = event[instant_name]
            instant_date = isoparse(instant['date'])
            instant_datetime = parse(value, default=instant_date)

            instant['date'] = None  # clear all-day date
            instant['dateTime'] = instant_datetime.isoformat()
            instant['timeZone'] = cal['timeZone']


class Url(Handler):
    """Handler for HTML and legacy Hangout links."""

    fieldnames = list(URL_PROPS.keys())

    @classmethod
    def get(cls, event):
        return [event.get(prop, '') for prop in URL_PROPS.values()]

    @classmethod
    def patch(cls, cal, event, fieldname, value):
        if fieldname == 'html_link':
            raise ReadonlyError(fieldname,
                                'It is not possible to verify that the value '
                                'has not changed. '
                                'Remove it from the input.')

        prop = URL_PROPS[fieldname]

        # Fail if the current value doesn't
        # match the desired patch. This requires an additional API query for
        # each row, so best to avoid attempting to update these fields.

        curr_value = event.get(prop, '')

        if curr_value != value:
            raise ReadonlyCheckError(fieldname, curr_value, value)


class Conference(Handler):
    """Handler for videoconference and teleconference details."""

    fieldnames = list(ENTRY_POINT_PROPS.keys())

    @classmethod
    def get(cls, event):
        if 'conferenceData' not in event:
            return ['', '']

        data = event['conferenceData']

        # only display first entry point for TSV
        # https://github.com/insanum/gcalcli/issues/533
        entry_point = data['entryPoints'][0]

        return [entry_point.get(prop, '')
                for prop in ENTRY_POINT_PROPS.values()]

    @classmethod
    def patch(cls, cal, event, fieldname, value):
        if not value:
            return

        prop = ENTRY_POINT_PROPS[fieldname]

        data = event.setdefault('conferenceData', {})
        entry_points = data.setdefault('entryPoints', [])
        if not entry_points:
            entry_points.append({})

        entry_point = entry_points[0]
        entry_point[prop] = value


class Title(SingleFieldHandler):
    """Handler for title."""

    fieldnames = ['title']

    @classmethod
    def _get(cls, event):
        return _valid_title(event)

    @classmethod
    def _patch(cls, event, value):
        event['summary'] = value


class Location(SimpleSingleFieldHandler):
    """Handler for location."""

    fieldnames = ['location']


class Description(SimpleSingleFieldHandler):
    """Handler for description."""

    fieldnames = ['description']


class Calendar(SingleFieldHandler):
    """Handler for calendar."""

    fieldnames = ['calendar']

    @classmethod
    def _get(cls, event):
        return event['gcalcli_cal']['summary']

    @classmethod
    def patch(cls, cal, event, fieldname, value):
        curr_value = cal['summary']

        if curr_value != value:
            raise ReadonlyCheckError(fieldname, curr_value, value)


class Email(SingleFieldHandler):
    """Handler for emails."""

    fieldnames = ['email']

    @classmethod
    def _get(cls, event):
        return event['creator'].get('email', '')


class ID(SimpleSingleFieldHandler):
    """Handler for event ID."""

    fieldnames = ['id']


class Action(SimpleSingleFieldHandler):
    """Handler specifying event processing during an update."""

    fieldnames = ['action']

    @classmethod
    def _get(cls, event):
        return ACTION_DEFAULT


HANDLERS = OrderedDict([('id', ID),
                        ('time', Time),
                        ('url', Url),
                        ('conference', Conference),
                        ('title', Title),
                        ('location', Location),
                        ('description', Description),
                        ('calendar', Calendar),
                        ('email', Email),
                        ('action', Action)])
HANDLERS_READONLY = {Url, Calendar}

FIELD_HANDLERS = dict(chain.from_iterable(
    (((fieldname, handler)
      for fieldname in handler.fieldnames)
     for handler in HANDLERS.values())))

FIELDNAMES_READONLY = frozenset(fieldname
                                for fieldname, handler
                                in FIELD_HANDLERS.items()
                                if handler in HANDLERS_READONLY)

_DETAILS_WITHOUT_HANDLERS = ['length', 'reminders', 'attendees',
                             'attachments', 'end']

DETAILS = list(HANDLERS.keys()) + _DETAILS_WITHOUT_HANDLERS
DETAILS_DEFAULT = {'time', 'title'}
