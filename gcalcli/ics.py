"""Helpers for working with iCal/ics format."""

from dataclasses import dataclass
import importlib.util
import io
from datetime import datetime, timedelta
import pathlib
import tempfile
from typing import Any, NamedTuple, Optional

from gcalcli.printer import Printer
from gcalcli.utils import localize_datetime


@dataclass
class EventData:
    body: Optional[dict[str, Any]]
    source: Any

    def label_str(self):
        if getattr(self.source, 'summary'):
            return f'"{self.source.summary}"'
        elif hasattr(self.source, 'dtstart') and self.source.dtstart.value:
            return f"with start {self.source.dtstart.value}"
        else:
            return None


class IcalData(NamedTuple):
    events: list[EventData]
    raw_components: list[Any]


def has_vobject_support() -> bool:
    return importlib.util.find_spec('vobject') is not None


def get_ics_data(
    ics: io.TextIOBase, verbose: bool, default_tz: str, printer: Printer
) -> IcalData:
    import vobject

    events: list[EventData] = []
    raw_components: list[Any] = []
    for v in vobject.readComponents(ics):
        if v.name == 'VCALENDAR' and hasattr(v, 'components'):
            raw_components.extend(
                c for c in v.components() if c.name != 'VEVENT'
            )
        # Strangely, in empty calendar cases vobject sometimes returns
        # Components with no vevent_list attribute at all.
        vevents = getattr(v, 'vevent_list', [])
        events.extend(
            CreateEventFromVOBJ(
                ve, verbose=verbose, default_tz=default_tz, printer=printer
            )
            for ve in vevents
        )
    return IcalData(events, raw_components)


def CreateEventFromVOBJ(
    ve, verbose: bool, default_tz: str, printer: Printer
) -> EventData:
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

    if not hasattr(ve, 'dtstart') or not ve.dtstart.value:
        printer.err_msg('Error: event does not have a dtstart!\n')
        return EventData(body=None, source=ve)

    if hasattr(ve, 'rrule'):
        if verbose:
            print('Recurrence...%s' % ve.rrule.value)

        event['recurrence'] = ['RRULE:' + ve.rrule.value]

    if verbose:
        print('Start........%s' % ve.dtstart.value.isoformat())
        print('Local Start..%s' % localize_datetime(ve.dtstart.value))

    # XXX
    # Timezone madness! Note that we're using the timezone for the calendar
    # being added to. This is OK if the event is in the same timezone. This
    # needs to be changed to use the timezone from the DTSTART and DTEND values.
    # Problem is, for example, the TZID might be "Pacific Standard Time" and
    # Google expects a timezone string like "America/Los_Angeles". Need to find
    # a way in python to convert to the more specific timezone string.
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

    # All events must have a start, but explicit end is optional.
    # If there is no end, use the duration if available, or the start otherwise.
    if hasattr(ve, 'dtend') and ve.dtend.value:
        end = ve.dtend.value
        if verbose:
            print('End..........%s' % end.isoformat())
            print('Local End....%s' % localize_datetime(end))
    else:  # using duration instead of end
        if hasattr(ve, 'duration') and ve.duration.value:
            duration = ve.duration.value
        else:
            printer.msg(
                "Falling back to 30m duration for imported event w/o "
                "explicit duration or end.\n"
            )
            duration = timedelta(minutes=30)
        if verbose:
            print('Duration.....%s' % duration)
        end = ve.dtstart.value + duration
        if verbose:
            print('Calculated End........%s' % end.isoformat())
            print('Calculated Local End..%s' % localize_datetime(end))

    if isinstance(end, datetime):
        event['end'] = {'dateTime': end.isoformat(), 'timeZone': default_tz}
    else:
        event['end'] = {'date': end.isoformat()}

    # NOTE: Reminders added by GoogleCalendarInterface caller.

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

    return EventData(body=event, source=ve)


def dump_partial_ical(
    events: list[EventData], raw_components: list[Any]
) -> pathlib.Path:
    import vobject

    tmp_dir = pathlib.Path(tempfile.mkdtemp(prefix="gcalcli."))
    f_path = tmp_dir.joinpath("rej.ics")
    cal = vobject.iCalendar()
    for c in raw_components:
        cal.add(c)
    for event in events:
        cal.add(event.source)
    with open(f_path, 'w') as f:
        f.write(cal.serialize())
    return f_path
