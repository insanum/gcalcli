import os
import pathlib
from typing import Optional

import platformdirs

from . import __program__


def default_data_dir() -> pathlib.Path:
    return platformdirs.user_data_path(__program__)


def data_file_paths(
        name: str,
        config_dir: Optional[pathlib.Path] = None,
    ) -> list[pathlib.Path]:
    """Return all paths actively used for the given data file name.

    The paths are returned with the preferred path first followed by any other
    detected legacy paths in order of decreasing precedence.
    """
    paths = [default_data_dir().joinpath(name)]
    legacy_path = (config_dir.joinpath(name)
                   if config_dir
                   else pathlib.Path(f'~/.gcalcli_{name}').expanduser())
    if legacy_path.exists():
        paths.append(legacy_path)
    return paths


def explicit_config_path() -> Optional[pathlib.Path]:
    config_path = os.environ.get('GCALCLI_CONFIG')
    return pathlib.Path(config_path) if config_path else None


def config_dir() -> pathlib.Path:
    from_env = explicit_config_path()
    if from_env:
        return from_env.parent if from_env.is_file() else from_env
    return pathlib.Path(platformdirs.user_config_dir(__program__))


def config_file() -> pathlib.Path:
    config_path = explicit_config_path()
    if config_path and config_path.is_file():
        # Special case: $GCALCLI_CONFIG points directly to file, not necessarily
        # named "config.toml".
        return config_path
    if not config_path:
        config_path = pathlib.Path(platformdirs.user_config_dir(__program__))
    return config_path.joinpath('config.toml')
