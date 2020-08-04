"""Handlers for specific details of events."""

from collections import OrderedDict
from itertools import chain
from typing import List, Optional

FMT_DATE = '%Y-%m-%d'
FMT_TIME = '%H:%M'


def _valid_title(event):
    if 'summary' in event and event['summary'].strip():
        return event['summary']
    else:
        return '(No title)'


class Handler:
    """Handler for a specific detail of an event."""

    # list of strings for fieldnames provided by this object
    # XXX: py36+: change to `fieldnames: List[str]`
    fieldnames = None  # type: Optional[List[str]]

    @classmethod
    def get(cls, event):
        """Return simple string representation for columnar output."""
        raise NotImplementedError

    @classmethod
    def patch(cls, event, value):
        """Patch event from value."""
        raise NotImplementedError


class SingleFieldHandler(Handler):
    """Handler for a detail that only produces one column."""

    @classmethod
    def get(cls, event):
        return [cls._get(event).strip()]


class SimpleSingleFieldHandler(SingleFieldHandler):
    """Handler for single-string details that require no special processing."""

    @classmethod
    def _get(cls, event):
        return event.get(cls.fieldnames[0], '')

    @classmethod
    def patch(cls, event, value):
        event[cls.fieldnames[0]] = value


class Time(Handler):
    """Handler for dates and times."""

    fieldnames = ['start_date', 'start_time', 'end_date', 'end_time']

    @classmethod
    def get(cls, event):
        return [event['s'].strftime(FMT_DATE), event['s'].strftime(FMT_TIME),
                event['e'].strftime(FMT_DATE), event['e'].strftime(FMT_TIME)]


class Url(Handler):
    """Handler for HTML and legacy Hangout links."""

    fieldnames = ['html_link', 'hangout_link']

    @classmethod
    def get(cls, event):
        return [event.get('htmlLink', ''),
                event.get('hangoutLink', '')]


class Conference(Handler):
    """Handler for videoconference and teleconference details."""

    fieldnames = ['conference_entry_point_type', 'conference_uri']

    @classmethod
    def get(cls, event):
        if 'conferenceData' not in event:
            return ['', '']

        data = event['conferenceData']

        # only display first entry point for TSV
        # https://github.com/insanum/gcalcli/issues/533
        entry_point = data['entryPoints'][0]

        return [entry_point['entryPointType'], entry_point['uri']]


class Title(SingleFieldHandler):
    """Handler for title."""

    fieldnames = ['title']

    @classmethod
    def _get(cls, event):
        return _valid_title(event)

    @classmethod
    def patch(cls, event, value):
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


class Email(SingleFieldHandler):
    """Handler for emails."""

    fieldnames = ['email']

    @classmethod
    def _get(cls, event):
        return event['creator'].get('email', '')


class ID(SimpleSingleFieldHandler):
    """Handler for event ID."""

    fieldnames = ['id']


HANDLERS_DEFAULT = {'time', 'title'}

HANDLERS = OrderedDict([('id', ID),
                        ('time', Time),
                        ('url', Url),
                        ('conference', Conference),
                        ('title', Title),
                        ('location', Location),
                        ('description', Description),
                        ('calendar', Calendar),
                        ('email', Email)])

FIELD_HANDLERS = dict(chain.from_iterable(
    (((fieldname, handler)
      for fieldname in handler.fieldnames)
     for handler in HANDLERS.values())))

_DETAILS_WITHOUT_HANDLERS = ['length', 'reminders', 'attendees',
                             'attachments', 'end']

DETAILS = list(HANDLERS.keys()) + _DETAILS_WITHOUT_HANDLERS