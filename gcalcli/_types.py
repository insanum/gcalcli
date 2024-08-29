#!/usr/bin/env python
"""_types.py: types for type inference."""

# must have underscore so as not to shadow stdlib types.py

from datetime import datetime
from typing import Any, TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from googleapiclient._apis.calendar.v3.schemas import (  # type: ignore
        CalendarListEntry,
        Event as GoogleEvent
    )

    class Event(GoogleEvent):
        """GoogleEvent, extended with some convenience attributes."""

        gcalcli_cal: CalendarListEntry
        s: datetime
        e: datetime

    # XXX: having all_cals available as an invariant would be better than
    # setting total=False
    class Cache(TypedDict, total=False):
        all_cals: list[CalendarListEntry]
else:
    CalendarListEntry = dict[str, Any]
    Event = dict[str, Any]
    Cache = dict[str, Any]
