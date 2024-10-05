import os
import pathlib
from typing import Optional, Tuple

import platformdirs

from . import __program__


def default_data_dir() -> pathlib.Path:
    return platformdirs.user_data_path(__program__)


def data_file_paths(
        name: str,
        config_dir: Optional[pathlib.Path] = None,
    ) -> list[Tuple[pathlib.Path, int]]:
    """Return all paths actively used for the given data file name.

    The paths are returned as tuples in order of decreasing precedence like:
    [(CONFIG/name, 1), (DATA_DIR/name, 0), (~/.gcalcli_{name}, -1)]
    with the DATA_DIR path always present and others only present if the file
    exists.
    """
    paths = []
    # Path in config dir takes precedence, if any.
    if config_dir:
        path_in_config = config_dir.joinpath(name)
        if path_in_config.exists():
            paths.append((path_in_config, 1))
    # Standard data path comes next.
    paths.append((default_data_dir().joinpath(name), 0))
    # Lastly, fall back to legacy path if it exists and there's no config dir.
    legacy_path = pathlib.Path(f'~/.gcalcli_{name}').expanduser()
    if legacy_path.exists():
        paths.append((legacy_path, -1))
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
