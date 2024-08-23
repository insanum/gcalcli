from datetime import datetime

from dateutil.tz import tzlocal

from gcalcli.conflicts import ShowConflicts

minimal_event = {
                    'e': datetime(2019, 1, 8, 15, 15, tzinfo=tzlocal()),
                    'id': 'minimal_event',
                    's': datetime(2019, 1, 8, 14, 15, tzinfo=tzlocal())
                 }
minimal_event_overlapping = {
                    'e': datetime(2019, 1, 8, 16, 15, tzinfo=tzlocal()),
                    'id': 'minimal_event_overlapping',
                    's': datetime(2019, 1, 8, 14, 30, tzinfo=tzlocal())
                 }
minimal_event_nonoverlapping = {
                    'e': datetime(2019, 1, 8, 16, 15, tzinfo=tzlocal()),
                    'id': 'minimal_event_nonoverlapping',
                    's': datetime(2019, 1, 8, 15, 30, tzinfo=tzlocal())
                 }


def test_finds_no_conflicts_for_one_event():
    """Basic test that only ensures the function can be run without error"""
    conflicts = []
    show_conflicts = ShowConflicts(conflicts.append)
    show_conflicts.show_conflicts(minimal_event)
    assert conflicts == []


def test_finds_conflicts_for_second_overlapping_event():
    conflicts = []
    show_conflicts = ShowConflicts(conflicts.append)
    show_conflicts.show_conflicts(minimal_event)
    show_conflicts.show_conflicts(minimal_event_overlapping)
    assert conflicts == [minimal_event]


def test_does_not_find_conflict_for_second_non_overlapping_event():
    conflicts = []
    show_conflicts = ShowConflicts(conflicts.append)
    show_conflicts.show_conflicts(minimal_event)
    show_conflicts.show_conflicts(minimal_event_nonoverlapping)
    assert conflicts == []
