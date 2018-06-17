from gcalcli.color_printer import ColorPrinter, COLOR_NAMES
from gcalcli.gcalcli import _u  # handles py2/py3 text compatibility
from io import StringIO
import sys


def test_init():
    cp = ColorPrinter()
    assert cp


def test_all_colors():
    """Makes sure the COLOR_NAMES is in sync with the colors in the printer"""
    cp = ColorPrinter()
    for color_name in COLOR_NAMES:
        out = StringIO()
        cp.msg(_u('msg'), color_name, file=out)
        out.seek(0)
        assert out.read() == _u(cp.colors[color_name] + 'msg' + '\033[0m')


def test_red_msg():
    cp = ColorPrinter()
    out = StringIO()
    cp.msg(_u('msg'), 'red', file=out)
    out.seek(0)
    assert out.read() == _u('\033[0;31mmsg\033[0m')


def test_err_msg(monkeypatch):
    err = StringIO()
    monkeypatch.setattr(sys, 'stderr', err)
    cp = ColorPrinter()
    cp.err_msg(_u('error'))
    err.seek(0)
    assert err.read() == _u('\033[31;1merror\033[0m')


def test_debug_msg(monkeypatch):
    err = StringIO()
    monkeypatch.setattr(sys, 'stderr', err)
    cp = ColorPrinter()
    cp.debug_msg(_u('debug'))
    err.seek(0)
    assert err.read() == _u('\033[0;33mdebug\033[0m')


def test_conky_red_msg():
    cp = ColorPrinter(conky=True)
    out = StringIO()
    cp.msg(_u('msg'), 'red', file=out)
    out.seek(0)
    assert out.read() == _u('${color red}msg')


def test_conky_err_msg(monkeypatch):
    err = StringIO()
    monkeypatch.setattr(sys, 'stderr', err)
    cp = ColorPrinter(conky=True)
    cp.err_msg(_u('error'))
    err.seek(0)
    assert err.read() == _u('${color red}error')


def test_conky_debug_msg(monkeypatch):
    err = StringIO()
    monkeypatch.setattr(sys, 'stderr', err)
    cp = ColorPrinter(conky=True)
    cp.debug_msg(_u('debug'))
    err.seek(0)
    assert err.read() == _u('${color yellow}debug')


def test_no_color():
    cp = ColorPrinter(use_color=False)
    out = StringIO()
    cp.msg(_u('msg'), 'red', file=out)
    out.seek(0)
    assert out.read() == _u('msg')
