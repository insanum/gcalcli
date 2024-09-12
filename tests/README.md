# Tests for gcalcli

This directory contains unit tests and functional tests for gcalcli. To run them all, make sure
you've installed [tox](https://tox.wiki/) and a supported python version, then in the repository root dir run

```shell
git submodule update --init
tox
```

Or run individual configurations like

```shell
tox -e py38,cli
```

The supported tox testing envs are listed and configured in ../tox.ini.

They're also configured to run on GitHub pull requests for various platforms and python versions
(config: ../.github/workflows/tests.yml).

## Linters and type checking

Tox will also run [Ruff](https://docs.astral.sh/ruff/) linters and [mypy](https://mypy-lang.org/)
type checking on the code (configured in the root dir, not under tests/).

If a weird Ruff check is giving you grief, you might need to
[ignore it](https://docs.astral.sh/ruff/settings/#lint_extend-per-file-ignores) in the pyproject.toml.

The type checking can also give you grief, particularly for library types it can't resolve. See
https://mypy.readthedocs.io/en/stable/common_issues.html for troubleshooting info. Some issues can
be resolved by using their stubgen tool to generate more type stubs under stubs/, or tweaking the
existing .pyi files there to better reflect reality.

## Unit tests

The python test files under tests/ are unit tests run via [pytest](https://pytest.org/). If you
hit failures, you can start a debugger with the --pdb flag to troubleshoot (probably also
specifying an individual test env and test to debug). Example:

```shell
tox -e py312 -- tests/test_gcalcli.py::test_import --pdb
```

## Functional cli tests

Under tests/cli/ there are also high-level tests running the cli in a shell using the
[Bats](https://bats-core.readthedocs.io/) tool. They have a .bats extension. These can be run
individually with `tox -e cli`.

NOTE: They'll fail if you haven't initialized the repo submodules for Bats yet, so if you hit
errors for missing test runner files, make sure you've run `git submodule update --init` in the
repo.

Some tests may fail on `assert_snapshot` calls from the
[bats-snapshot](https://github.com/markkong318/bats-snapshot) helper, in which case you can easily
update snapshots by finding and deleting the corresponding .snap file in \__snapshots__/, rerunning
the cli tests, and then reviewing the updated snapshot file to make sure the diff is expected.
