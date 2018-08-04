import gcalcli.utils as utils
from datetime import datetime
from dateutil.tz import UTC
import six
import pytest


def test_get_time_from_str():
    assert utils.get_time_from_str('7am tomorrow')


def test_get_times_from_duration():
    begin_1970 = '1970-01-01'
    begin_1970_midnight = begin_1970 + 'T00:00:00+00:00'
    two_hrs_later = begin_1970 + 'T02:00:00+00:00'
    next_day = '1970-01-02'
    assert (begin_1970_midnight, two_hrs_later) == \
        utils.get_times_from_duration(begin_1970_midnight, duration=120)

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


def test_u():
    for text in [b'text', 'text', '\u309f', u'\xe1', b'\xff\xff', 42]:
        if six.PY2:
            assert isinstance(utils._u(text), unicode)  # noqa: F821
        else:
            assert isinstance(utils._u(text), str)


def test_set_locale():
    with pytest.raises(ValueError):
        utils.set_locale('not_a_real_locale')
