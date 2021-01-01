"""Handlers for specific agendaupdate actions."""

from gcalcli.details import FIELD_HANDLERS, FIELDNAMES_READONLY
from gcalcli.exceptions import ReadonlyError


CONFERENCE_DATA_VERSION = 1


def _iter_field_handlers(row):
    for fieldname, value in row.items():
        handler = FIELD_HANDLERS[fieldname]
        yield fieldname, handler, value


def patch(row, cal, interface):
    """Patch event with new data."""
    curr_event = None
    mod_event = {}
    cal_id = cal['id']

    for fieldname, handler, value in _iter_field_handlers(row):
        if fieldname in FIELDNAMES_READONLY:
            # Instead of changing mod_event, the Handler.patch() for
            # a readonly field checks against the current values.

            if curr_event is None:
                # XXX: id must be an earlier column before anything
                # readonly. Otherwise, there will be no eventId for
                # get()

                curr_event = interface._retry_with_backoff(
                    interface.get_events()
                    .get(
                        calendarId=cal_id,
                        eventId=mod_event['id']
                    )
                )

            handler.patch(cal, curr_event, fieldname, value)
        else:
            handler.patch(cal, mod_event, fieldname, value)

    interface._retry_with_backoff(
        interface.get_events()
        .patch(
            calendarId=cal_id,
            eventId=mod_event['id'],
            conferenceDataVersion=CONFERENCE_DATA_VERSION,
            body=mod_event
        )
    )


def insert(row, cal, interface):
    """Insert new event."""
    event = {}
    cal_id = cal['id']

    for fieldname, handler, value in _iter_field_handlers(row):
        if fieldname in FIELDNAMES_READONLY:
            raise ReadonlyError("Cannot specify value on insert.")

        handler.patch(cal, event, fieldname, value)

    interface._retry_with_backoff(
        interface.get_events()
        .insert(
            calendarId=cal_id,
            conferenceDataVersion=CONFERENCE_DATA_VERSION,
            body=event
        )
    )


def delete(row, cal, interface):
    """Delete event."""
    cal_id = cal['id']
    event_id = row['id']

    interface.delete(cal_id, event_id)


def ignore(*args, **kwargs):
    """Do nothing."""


ACTIONS = {"patch", "insert", "delete", "ignore"}
