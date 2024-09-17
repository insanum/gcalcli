"""Helpers for working with iCal/ics format."""

import importlib.util
import io
from datetime import datetime
from typing import Any, Optional

from gcalcli.printer import Printer
from gcalcli.utils import localize_datetime

EventBody = dict[str, Any]


def has_vobject_support() -> bool:
    return importlib.util.find_spec('vobject') is not None


def get_events(
    ics: io.TextIOBase, verbose: bool, default_tz: str, printer: Printer
) -> list[Optional[EventBody]]:
    import vobject

    events: list[Optional[EventBody]] = []
    for v in vobject.readComponents(ics):
        # Strangely, in empty calendar cases vobject sometimes returns
        # Components with no vevent_list attribute at all.
        vevents = getattr(v, 'vevent_list', [])
        events.extend(
            CreateEventFromVOBJ(
                ve, verbose=verbose, default_tz=default_tz, printer=printer
            )
            for ve in vevents
        )
    return events


def CreateEventFromVOBJ(
    ve, verbose: bool, default_tz: str, printer: Printer
) -> Optional[EventBody]:
    event = {}

    if verbose:
        print('+----------------+')
        print('| Calendar Event |')
        print('+----------------+')

    if hasattr(ve, 'summary'):
        if verbose:
            print('Event........%s' % ve.summary.value)
        event['summary'] = ve.summary.value

    if hasattr(ve, 'location'):
        if verbose:
            print('Location.....%s' % ve.location.value)
        event['location'] = ve.location.value

    if not hasattr(ve, 'dtstart') or not hasattr(ve, 'dtend'):
        printer.err_msg('Error: event does not have a dtstart and dtend!\n')
        return None

    if verbose:
        if ve.dtstart.value:
            print('Start........%s' % ve.dtstart.value.isoformat())
        if ve.dtend.value:
            print('End..........%s' % ve.dtend.value.isoformat())
        if ve.dtstart.value:
            print('Local Start..%s' % localize_datetime(ve.dtstart.value))
        if ve.dtend.value:
            print('Local End....%s' % localize_datetime(ve.dtend.value))

    if hasattr(ve, 'rrule'):
        if verbose:
            print('Recurrence...%s' % ve.rrule.value)

        event['recurrence'] = ['RRULE:' + ve.rrule.value]

    if hasattr(ve, 'dtstart') and ve.dtstart.value:
        # XXX
        # Timezone madness! Note that we're using the timezone for the
        # calendar being added to. This is OK if the event is in the
        # same timezone. This needs to be changed to use the timezone
        # from the DTSTART and DTEND values. Problem is, for example,
        # the TZID might be "Pacific Standard Time" and Google expects
        # a timezone string like "America/Los_Angeles". Need to find a
        # way in python to convert to the more specific timezone
        # string.
        # XXX
        # print ve.dtstart.params['X-VOBJ-ORIGINAL-TZID'][0]
        # print default_tz
        # print dir(ve.dtstart.value.tzinfo)
        # print vars(ve.dtstart.value.tzinfo)

        start = ve.dtstart.value.isoformat()
        if isinstance(ve.dtstart.value, datetime):
            event['start'] = {'dateTime': start, 'timeZone': default_tz}
        else:
            event['start'] = {'date': start}

        # NOTE: Reminders added by GoogleCalendarInterface caller.

        # Can only have an end if we have a start, but not the other
        # way around apparently...  If there is no end, use the start
        if hasattr(ve, 'dtend') and ve.dtend.value:
            end = ve.dtend.value.isoformat()
            if isinstance(ve.dtend.value, datetime):
                event['end'] = {'dateTime': end, 'timeZone': default_tz}
            else:
                event['end'] = {'date': end}

        else:
            event['end'] = event['start']

    if hasattr(ve, 'description') and ve.description.value.strip():
        descr = ve.description.value.strip()
        if verbose:
            print('Description:\n%s' % descr)
        event['description'] = descr

    if hasattr(ve, 'organizer'):
        if ve.organizer.value.startswith('MAILTO:'):
            email = ve.organizer.value[7:]
        else:
            email = ve.organizer.value
        if verbose:
            print('organizer:\n %s' % email)
        event['organizer'] = {'displayName': ve.organizer.name, 'email': email}

    if hasattr(ve, 'attendee_list'):
        if verbose:
            print('attendees:')
        event['attendees'] = []
        for attendee in ve.attendee_list:
            if attendee.value.upper().startswith('MAILTO:'):
                email = attendee.value[7:]
            else:
                email = attendee.value
            if verbose:
                print(' %s' % email)

            event['attendees'].append(
                {'displayName': attendee.name, 'email': email}
            )

    if hasattr(ve, 'uid'):
        uid = ve.uid.value.strip()
        if verbose:
            print(f'UID..........{uid}')
        event['iCalUID'] = uid
    if hasattr(ve, 'sequence'):
        sequence = ve.sequence.value.strip()
        if verbose:
            print(f'Sequence.....{sequence}')
        event['sequence'] = sequence

    return event
