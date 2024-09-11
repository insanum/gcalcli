import pathlib
import shutil

try:
    import cPickle as pickle  # type: ignore
except Exception:
    import pickle

import googleapiclient.discovery

TEST_DATA_DIR = pathlib.Path(__file__).parent / 'data'


def test_legacy_certs(tmpdir, gcali_patches, patched_google_reauth):
    tmpdir = pathlib.Path(tmpdir)
    oauth_filepath = tmpdir / 'oauth'
    shutil.copy(TEST_DATA_DIR / 'legacy_oauth_creds.json', oauth_filepath)
    gcal = gcali_patches.GCalI(data_path=tmpdir, refresh_cache=False)
    assert isinstance(
        gcal.get_cal_service(), googleapiclient.discovery.Resource
    )
    with open(oauth_filepath, 'rb') as gcalcli_oauth:
        try:
            pickle.load(gcalcli_oauth)
        except Exception as e:
            raise AssertionError(
                f"Couldn't load oauth file as updated pickle format: {e}"
            )
