#!/bin/bash

BATS="./tests/cli/bats/bin/bats"
if [ ! -f $BATS ]; then
  echo "FAILED to run cli tests: Missing bats runner!" >&2
  echo "(Did you forget to run 'git submodule update --init'?)" >&2
  exit 1
fi
$BATS "$@"
