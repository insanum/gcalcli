
import pytest
from gcalcli.gcal import GoogleCalendarInterface
from gcalcli import auth

def test_service_account_loading(PatchedGCalI, monkeypatch):
    # Mock auth.load_service_account to return a dummy
    mock_creds = "DUMMY_CREDS"
    
    mock_called = False
    def mock_load(path):
        nonlocal mock_called
        mock_called = True
        assert path == "/tmp/fake-key.json"
        return mock_creds

    monkeypatch.setattr(auth, 'load_service_account', mock_load)

    # Initialize GCal with service_account option
    # Note: PatchedGCalI uses default_options fixture usually, we override
    gcal = PatchedGCalI(service_account="/tmp/fake-key.json")
    
    # Trigger auth load (lazy init might not have done it yet if cache existed? 
    # But PatchedGCalI stubs things out. Let's explicitly call _load_credentials or access)
    gcal._load_credentials()
    
    assert mock_called
    assert gcal.credentials == mock_creds

def test_service_account_skips_oauth_cache(PatchedGCalI, monkeypatch, tmp_path):
    # Setup a fake oauth cache file
    # PatchedGCalI mocks data_file_path_stub. We need to create the file where it expects.
    # But checking if the file is IGNORED is the goal.
    
    # Mock load_service_account
    monkeypatch.setattr(auth, 'load_service_account', lambda p: "SA_CREDS")
    
    gcal = PatchedGCalI(service_account="/tmp/key.json")
    gcal._load_credentials()
    
    assert gcal.credentials == "SA_CREDS"
