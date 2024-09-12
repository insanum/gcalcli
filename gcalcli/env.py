import os
import pathlib
import platformdirs

from . import __program__


def default_data_dir() -> pathlib.Path:
    return platformdirs.user_data_path(__program__)


def default_config_dir() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get('GCALCLI_CONFIG')
        or platformdirs.user_config_dir(__program__)
    )
