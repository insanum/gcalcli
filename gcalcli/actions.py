"""Handlers for specific agendaupdate actions."""

from gcalcli.details import FIELD_HANDLERS, FIELDNAMES_READONLY


CONFERENCE_DATA_VERSION = 1


def patch(row, cal, interface):
    """Patch event with new data."""
    curr_event = None
    mod_event = {}
    cal_id = cal['id']

    for fieldname, value in row.items():
        handler = FIELD_HANDLERS[fieldname]

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


def ignore(*args, **kwargs):
    """Do nothing."""


ACTIONS = {"patch", "ignore"}
