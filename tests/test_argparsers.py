from gcalcli import argparsers
import pytest


def test_module_import():
    assert argparsers


def test_search_parser():
    search_parser = argparsers.get_search_parser()
    with pytest.raises(SystemExit):
        search_parser.parse_args([])
