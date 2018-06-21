from gcalcli.utils import get_time_from_str, days_since_epoch, _u
from datetime import datetime
from dateutil.tz import UTC
import pytest


def test_get_time_from_str():
    begin_2018 = '2018-01-01'
    begin_2018_midnight = begin_2018 + 'T00:00:00+00:00'
    two_hrs_later = begin_2018 + 'T02:00:00+00:00'
    next_day = '2018-01-02'
    assert (begin_2018_midnight, two_hrs_later) == \
        get_time_from_str(begin_2018_midnight, duration=120)

    assert (begin_2018, next_day) == \
        get_time_from_str(begin_2018_midnight, duration=1, allday=True)

    with pytest.raises(ValueError):
        get_time_from_str('this is not a date')

    with pytest.raises(ValueError):
        get_time_from_str(begin_2018_midnight, duration='not a duration')

    with pytest.raises(ValueError):
        get_time_from_str(
                begin_2018_midnight, duration='not a duraction', allday=True)


def test_days_since_epoch():
    assert days_since_epoch(datetime(1970, 1, 1, 0, tzinfo=UTC)) == 0
    assert days_since_epoch(datetime(1970, 12, 31)) == 364


def test_u():
    for text in [b'text', 'text', '\u309f']:
        assert isinstance(_u(text), str)
