setup() {
  load 'test_helper/bats-support/load'
  load 'test_helper/bats-assert/load'
  load 'test_helper/bats-file/load'
  load 'test_helper/bats-snapshot/load'

  TEST_HOME_DIR="$(temp_make)"
  export HOME="$TEST_HOME_DIR"
  export GCALCLI_USERLESS_MODE=1
}

function teardown() {
  temp_del "$TEST_HOME_DIR"
}

@test "can run" {
  run gcalcli
  assert_failure 2
  assert_output --regexp 'usage: .*error:.*required: .*command'
}

@test "prints correct help" {
  GCALCLI_CONFIG=/some/gcalcli/config COLUMNS=72 run gcalcli -h
  assert_success
  assert_snapshot
}

@test "can run init" {
  run gcalcli init --client-id=SOME_CLIENT <<< "SOME_SECRET
"
  assert_snapshot
}

@test "can run add" {
  run gcalcli add <<< "sometitle

tomorrow


."
  assert_snapshot
}
