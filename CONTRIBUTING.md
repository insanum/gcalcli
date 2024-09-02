# Contributing to gcalcli

Welcome! Glad you're interested in contributing to the project. ❤️

> If you want to support the project, there are plenty of other ways to show support besides writing code:
> - Use the app and help catch issues
> - Help troubleshoot other users' issues in the tracker
> - Suggest improvements to instructions and documentation

## Community

The issue tracker at https://github.com/insanum/gcalcli is the best place to reach out to maintainers or get help contributing.

## Code of Conduct

Please strive to show respect and be welcoming of everyone.

Please report unacceptable behavior to david AT mumind DOT me.

## Code review

To contribute changes, please send a pull request to https://github.com/insanum/gcalcli.

For nontrivial changes it's helpful to open a separate issue in the tracker to discuss the problem/idea, and to make sure tests are up-to-date and passing (see "Howto: Run tests" below).

### How reviews work

Generally a maintainer will be notified of the PR and follow up to review it. You can explicitly request review from @dbarnett if you prefer.

Feel free to comment to bump it for attention if nobody follows up after a week or so.

## Quality guidelines

For now, you can just check that the tests and linters are happy and work with reviewers if they raise other quality concerns.

Test coverage for new functionality is helpful, but not always required. Feel free to start reviews before you've finished writing tests and ask your reviewer for help implementing the right test coverage.

## Running tests

Make sure you've installed [tox](https://tox.wiki/) and a supported python version, then run

```shell
git submodule update --init
tox
```

NOTE: You'll also want to install the "dev" extra in any development environment you're using
that's not managed by tox (by changing install commands `gcalcli`->`gcalcli[dev]` or
`.`->`.[dev]`).

See [tests/README.md](tests/README.md) for more info on the tests.
