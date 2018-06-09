from gcalcli import gcalcli
import pytest


def test_ValidColor():
    with pytest.raises(Exception):
        gcalcli.ValidColor('not a valid color')
