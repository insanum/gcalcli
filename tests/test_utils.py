from datetime import datetime, timedelta

import pytest
from dateutil.tz import UTC, tzutc

from gcalcli import utils


def test_get_time_from_str():
    assert utils.get_time_from_str('7am tomorrow')


def test_get_parsed_timedelta_from_str():
    assert utils.get_timedelta_from_str('3.5h') == timedelta(
                                        hours=3, minutes=30)
    assert utils.get_timedelta_from_str('1') == timedelta(minutes=1)
    assert utils.get_timedelta_from_str('1m') == timedelta(minutes=1)
    assert utils.get_timedelta_from_str('1h') == timedelta(hours=1)
    assert utils.get_timedelta_from_str('1h1m') == timedelta(
                                        hours=1, minutes=1)
    assert utils.get_timedelta_from_str('1:10') == timedelta(
                                        hours=1, minutes=10)
    assert utils.get_timedelta_from_str('2d:1h:3m') == timedelta(
                                        days=2, hours=1, minutes=3)
    assert utils.get_timedelta_from_str('2d 1h 3m 10s') == timedelta(
                                        days=2, hours=1, minutes=3, seconds=10)
    assert utils.get_timedelta_from_str(
        '2 days 1 hour 2 minutes 40 seconds') == timedelta(
                                        days=2, hours=1, minutes=2, seconds=40)
    with pytest.raises(ValueError) as ve:
        utils.get_timedelta_from_str('junk')
    assert str(ve.value) == "Duration is invalid: junk"


def test_get_times_from_duration():
    begin_1970 = '1970-01-01'
    begin_1970_midnight = begin_1970 + 'T00:00:00+00:00'
    two_hrs_later = begin_1970 + 'T02:00:00+00:00'
    next_day = '1970-01-02'
    assert (begin_1970_midnight, two_hrs_later) == \
        utils.get_times_from_duration(begin_1970_midnight, duration=120)

    assert (begin_1970_midnight, two_hrs_later) == \
        utils.get_times_from_duration(
            begin_1970_midnight, duration="2h")

    assert (begin_1970_midnight, two_hrs_later) == \
        utils.get_times_from_duration(
            begin_1970_midnight, duration="120m")

    assert (begin_1970, next_day) == \
        utils.get_times_from_duration(
            begin_1970_midnight, duration=1, allday=True)

    with pytest.raises(ValueError):
        utils.get_times_from_duration('this is not a date')

    with pytest.raises(ValueError):
        utils.get_times_from_duration(
            begin_1970_midnight, duration='not a duration')

    with pytest.raises(ValueError):
        utils.get_times_from_duration(
                begin_1970_midnight, duration='not a duraction', allday=True)


def test_days_since_epoch():
    assert utils.days_since_epoch(datetime(1970, 1, 1, 0, tzinfo=UTC)) == 0
    assert utils.days_since_epoch(datetime(1970, 12, 31)) == 364


def test_set_locale():
    with pytest.raises(ValueError):
        utils.set_locale('not_a_real_locale')


def test_localize_datetime(PatchedGCalI):
    dt = utils.localize_datetime(datetime.now())
    assert dt.tzinfo is not None

    dt = datetime.now(tzutc())
    dt = utils.localize_datetime(dt)
    assert dt.tzinfo is not None
