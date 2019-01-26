import os

import gcalcli.validators


def test_edit_event_description(capsys, monkeypatch,
                                PatchedGCalIForEvents, default_options):
    # we need a func to pass into gcalcli.validators.validate_input
    def _useless():
        pass
    # we need a way to be able to jump out of the edit loop
    # set an env variable here, then change it after the first
    # choice, which is the one we want to test - the second
    #
    os.environ['GCALCLI_TEST_CYCLE'] = "0"
    # set opts so we send current to stdout
    default_options.update(
        [("text", "Test event"), ("details", {"description": True})]
    )
    # we need to choose 'd' from edit menu
    monkeypatch.setattr(gcalcli.gcalcli, "edit_choice_input",
                        lambda: "d")
    # we set a new description at the prompt
    monkeypatch.setattr(gcalcli.validators, "validate_input",
                        lambda _useless: "Added Desc")
    gcal = PatchedGCalIForEvents(**(default_options))
    gcal.ModifyEvents(gcal._edit_event, default_options)
    captured = capsys.readouterr()
    os.environ.pop('GCALCLI_TEST_CYCLE')
    assert "Added Desc" in captured.out


def test_remove_event_description(capsys, monkeypatch,
                                  PatchedGCalIForEvents, default_options):
    # we need a func to pass into gcalcli.validators.validate_input
    def _useless():
        pass
    # we need a way to be able to jump out of the edit loop
    # set an env variable here, then change it after the first
    # choice, which is the one we want to test - the second
    #
    os.environ['GCALCLI_TEST_CYCLE'] = "0"
    # set opts so we send current to stdout
    default_options.update(
        [("text", "Test event"), ("details", {"description": True})]
    )
    # we need to choose 'd' from edit menu
    monkeypatch.setattr(gcalcli.gcalcli, "edit_choice_input",
                        lambda: "d")
    # we use a '.' at the prompt to remove the current value
    monkeypatch.setattr(gcalcli.validators, "validate_input",
                        lambda _useless: ".")
    gcal = PatchedGCalIForEvents(**(default_options))
    gcal.ModifyEvents(gcal._edit_event, default_options)
    captured = capsys.readouterr()
    os.environ.pop('GCALCLI_TEST_CYCLE')
    assert "TEST DESCRIPTION" not in captured.out


def test_edit_event_location(capsys, monkeypatch,
                             PatchedGCalIForEvents, default_options):
    # we need a func to pass into gcalcli.validators.validate_input
    def _useless():
        pass
    # we need a way to be able to jump out of the edit loop
    # set an env variable here, then change it after the first
    # choice, which is the one we want to test - the second
    #
    os.environ['GCALCLI_TEST_CYCLE'] = "0"
    # set opts so we send current to stdout
    default_options.update(
        [("text", "Test event"),
         ("details", {"description": True, "location": True, "width": 80})
         ])
    # we need to choose 'l' from edit menu
    monkeypatch.setattr(gcalcli.gcalcli, "edit_choice_input",
                        lambda: "l")
    # we set a new location at the prompt
    monkeypatch.setattr(gcalcli.validators, "validate_input",
                        lambda _useless: "New Location")
    gcal = PatchedGCalIForEvents(**(default_options))
    gcal.ModifyEvents(gcal._edit_event, default_options)
    captured = capsys.readouterr()
    os.environ.pop('GCALCLI_TEST_CYCLE')
    assert "New Location" in captured.out


def test_remove_event_location(capsys, monkeypatch,
                               PatchedGCalIForEvents, default_options):
    # we need a func to pass into gcalcli.validators.validate_input
    def _useless():
        pass
    # we need a way to be able to jump out of the edit loop
    # set an env variable here, then change it after the first
    # choice, which is the one we want to test - the second
    #
    os.environ['GCALCLI_TEST_CYCLE'] = "0"
    # set opts so we send current to stdout
    default_options.update(
        [("text", "Test event"),
         ("details", {"description": True, "location": True, "width": 80})
         ])
    # we need to choose 'l' from edit menu
    monkeypatch.setattr(gcalcli.gcalcli, "edit_choice_input",
                        lambda: "l")
    # we use a '.' at the prompt to remove the current value
    monkeypatch.setattr(gcalcli.validators, "validate_input",
                        lambda _useless: ".")
    gcal = PatchedGCalIForEvents(**(default_options))
    gcal.ModifyEvents(gcal._edit_event, default_options)
    captured = capsys.readouterr()
    os.environ.pop('GCALCLI_TEST_CYCLE')
    assert "Neverwhere" not in captured.out
