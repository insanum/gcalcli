from gcalcli.color_printer import ColorPrinter, COLOR_NAMES
from io import BytesIO
import sys
import pytest

def test_init():
    cp = ColorPrinter()
    assert cp


def test_all_colors():
    """Makes sure the COLOR_NAMES is in sync with the colors in the printer"""
    cp = ColorPrinter()
    for color_name in COLOR_NAMES:
        out = BytesIO()
        cp.msg('msg', color_name, file=out)
        out.seek(0)
        assert out.read() == cp.colors[color_name] + 'msg' + '\033[0m'


def test_red_msg():
    cp = ColorPrinter()
    out = BytesIO()
    cp.msg('msg', 'red', file=out)
    out.seek(0)
    assert out.read() == '\033[31;1mmsg\033[0m'


def test_err_msg(monkeypatch):
    err = BytesIO()
    monkeypatch.setattr(sys, 'stderr', err)
    cp = ColorPrinter()
    cp.err_msg('error')
    err.seek(0)
    assert err.read() == '\033[31;1merror\033[0m'


def test_debug_msg(monkeypatch):
    err = BytesIO()
    monkeypatch.setattr(sys, 'stderr', err)
    cp = ColorPrinter()
    cp.debug_msg('debug')
    err.seek(0)
    assert err.read() == '\033[0;33mdebug\033[0m'


def test_conky_red_msg():
    cp = ColorPrinter(conky=True)
    out = BytesIO()
    cp.msg('msg', 'red', file=out)
    out.seek(0)
    assert out.read() == '${color red}msg'


def test_conky_err_msg(monkeypatch):
    err = BytesIO()
    monkeypatch.setattr(sys, 'stderr', err)
    cp = ColorPrinter(conky=True)
    cp.err_msg('error')
    err.seek(0)
    assert err.read() == '${color red}error'


def test_conky_err_msg(monkeypatch):
    err = BytesIO()
    monkeypatch.setattr(sys, 'stderr', err)
    cp = ColorPrinter(conky=True)
    cp.debug_msg('debug')
    err.seek(0)
    assert err.read() == '${color yellow}debug'


def test_no_color():
    cp = ColorPrinter(use_color=False)
    out = BytesIO()
    cp.msg('msg', 'red', file=out)
    out.seek(0)
    assert out.read() == 'msg'
