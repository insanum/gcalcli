"""Handlers for specific details of events."""

from collections import OrderedDict
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

    # list of strings for headers provided by this object
    # XXX: py36+: change to `header: List[str]`
    header = None  # type: Optional[List[str]]

    @classmethod
    def get(cls, event):
        """Return simple string representation for columnar output."""
        raise NotImplementedError


class SingleColumnHandler(Handler):
    """Handler for a detail that only produces one column."""

    @classmethod
    def get(cls, event):
        return [cls._get(event).strip()]


class SimpleSingleColumnHandler(SingleColumnHandler):
    """Handler for single-string details that require no special processing."""

    # XXX: py36+: change to `_key: str`
    _key = None  # type: Optional[str]

    @property
    def header(self):
        """Getter property that returns a list of `self._key`."""
        return [self._key]

    @classmethod
    def _get(cls, event):
        return event.get(cls._key, '')


class Time(Handler):
    """Handler for dates and times."""

    header = ['start_date', 'start_time', 'end_date', 'end_time']

    @classmethod
    def get(cls, event):
        return [event['s'].strftime(FMT_DATE), event['s'].strftime(FMT_TIME),
                event['e'].strftime(FMT_DATE), event['e'].strftime(FMT_TIME)]


class Url(Handler):
    """Handler for HTML and legacy Hangout links."""

    header = ['html_link', 'hangout_link']

    @classmethod
    def get(cls, event):
        return [event.get('htmlLink', ''),
                event.get('hangoutLink', '')]


class Conference(Handler):
    """Handler for videoconference and teleconference details."""

    header = ['conference_entry_point_type', 'conference_uri']

    @classmethod
    def get(cls, event):
        if 'conferenceData' not in event:
            return ['', '']

        data = event['conferenceData']

        # only display first entry point for TSV
        # https://github.com/insanum/gcalcli/issues/533
        entry_point = data['entryPoints'][0]

        return [entry_point['entryPointType'], entry_point['uri']]


class Title(SingleColumnHandler):
    """Handler for title."""

    header = ['title']

    @classmethod
    def _get(cls, event):
        return _valid_title(event)


class Location(SimpleSingleColumnHandler):
    """Handler for location."""

    _key = 'location'


class Description(SimpleSingleColumnHandler):
    """Handler for description."""

    _key = 'description'


class Calendar(SingleColumnHandler):
    """Handler for calendar."""

    header = ['calendar']

    @classmethod
    def _get(cls, event):
        return event['gcalcli_cal']['summary']


class Email(SingleColumnHandler):
    """Handler for emails."""

    header = ['email']

    @classmethod
    def _get(cls, event):
        return event['creator'].get('email', '')


HANDLERS_DEFAULT = {'time', 'title'}

HANDLERS = OrderedDict([('time', Time),
                        ('url', Url),
                        ('conference', Conference),
                        ('title', Title),
                        ('location', Location),
                        ('description', Description),
                        ('calendar', Calendar),
                        ('email', Email)])

_DETAILS_WITHOUT_HANDLERS = ['length', 'reminders', 'attendees',
                             'attachments', 'end']

DETAILS = list(HANDLERS.keys()) + _DETAILS_WITHOUT_HANDLERS
