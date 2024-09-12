setup() {
  load 'test_helper/bats-support/load'
  load 'test_helper/bats-assert/load'
  load 'test_helper/bats-snapshot/load'
  export GCALCLI_USERLESS_MODE=1
}

@test "can run" {
  run gcalcli
  assert_equal $status 2
  assert_output --regexp 'usage: .*error:.*required: .*command'
}

@test "prints correct help" {
  GCALCLI_CONFIG=/some/gcalcli/config COLUMNS=72 run gcalcli -h
  assert_success
  assert_snapshot
}

@test "can run add" {
  run gcalcli add <<< "sometitle

tomorrow


."
  assert_snapshot
}
