from gcalcli.cli import run_add_prompt
from argparse import Namespace
from gcalcli.printer import Printer


def test_run_add_prompt():
    """Basic test that only ensures the function can be run without error"""
    printer = Printer()
    min_keys = ['title', 'where', 'when', 'duration', 'description',
                'event_color', 'reminders']
    parsed_args = Namespace(**{k: 'test' for k in min_keys})
    run_add_prompt(parsed_args, printer)
