import sys
from argparse import ArgumentTypeError
from io import StringIO

import pytest
from gcalcli.printer import COLOR_NAMES, Printer, valid_color_name
from gcalcli.gcalcli import _u  # handles py2/py3 text compatibility


def test_init():
    cp = Printer()
    assert cp


def test_valid_color_name():
    with pytest.raises(ArgumentTypeError):
        valid_color_name('this_is_not_a_colorname')


def test_all_colors():
    """Makes sure the COLOR_NAMES is in sync with the colors in the printer"""
    cp = Printer()
    for color_name in COLOR_NAMES:
        out = StringIO()
        cp.msg(_u('msg'), color_name, file=out)
        out.seek(0)
        assert out.read() == _u(cp.colors[color_name] + 'msg' + '\033[0m')


def test_red_msg():
    cp = Printer()
    out = StringIO()
    cp.msg(_u('msg'), 'red', file=out)
    out.seek(0)
    assert out.read() == _u('\033[0;31mmsg\033[0m')


def test_err_msg(monkeypatch):
    err = StringIO()
    monkeypatch.setattr(sys, 'stderr', err)
    cp = Printer()
    cp.err_msg(_u('error'))
    err.seek(0)
    assert err.read() == _u('\033[31;1merror\033[0m')


def test_debug_msg(monkeypatch):
    err = StringIO()
    monkeypatch.setattr(sys, 'stderr', err)
    cp = Printer()
    cp.debug_msg(_u('debug'))
    err.seek(0)
    assert err.read() == _u('\033[0;33mdebug\033[0m')


def test_conky_red_msg():
    cp = Printer(conky=True)
    out = StringIO()
    cp.msg(_u('msg'), 'red', file=out)
    out.seek(0)
    assert out.read() == _u('${color red}msg')


def test_conky_err_msg(monkeypatch):
    err = StringIO()
    monkeypatch.setattr(sys, 'stderr', err)
    cp = Printer(conky=True)
    cp.err_msg(_u('error'))
    err.seek(0)
    assert err.read() == _u('${color red}error')


def test_conky_debug_msg(monkeypatch):
    err = StringIO()
    monkeypatch.setattr(sys, 'stderr', err)
    cp = Printer(conky=True)
    cp.debug_msg(_u('debug'))
    err.seek(0)
    assert err.read() == _u('${color yellow}debug')


def test_no_color():
    cp = Printer(use_color=False)
    out = StringIO()
    cp.msg(_u('msg'), 'red', file=out)
    out.seek(0)
    assert out.read() == _u('msg')


def test_extract_colorcodes():
    cp = Printer()
    test_event_string = _u('\x1b[0;35mTest Event')
    (event_string, color_string) = cp.extract_colorcodes(test_event_string, '')
    assert color_string == _u('\x1b[0;35m')
    assert event_string == 'Test Event'
