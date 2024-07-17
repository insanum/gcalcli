#!/usr/bin/env python
"""_types.py: types for type inference."""

# must have underscore so as not to shadow stdlib types.py

from datetime import datetime
from typing import Any, Dict, List, TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from googleapiclient._apis.calendar.v3.schemas \
        import CalendarListEntry, Event as GoogleEvent

    class Event(GoogleEvent):
        """GoogleEvent, extended with some convenience attributes."""

        gcalcli_cal: CalendarListEntry
        s: datetime
        e: datetime

    # XXX: having all_cals available as an invariant would be better than
    # setting total=False
    class Cache(TypedDict, total=False):
        all_cals: List[CalendarListEntry]
else:
    CalendarListEntry = Dict[str, Any]
    Event = Dict[str, Any]
    Cache = Dict[str, Any]
