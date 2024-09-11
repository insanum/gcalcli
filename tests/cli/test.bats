setup() {
  load 'test_helper/bats-support/load'
  load 'test_helper/bats-assert/load'
  load 'test_helper/bats-snapshot/load'
}

@test "can run" {
  run gcalcli
  assert_output --regexp 'usage: .*error:.*required: .*command'
}

@test "prints correct help" {
  run gcalcli -h
  assert_output --regexp 'positional arguments:.*list.*search.*edit.*options:'
}

@test "can run add" {
  GCALCLI_USERLESS_MODE=1 run gcalcli add <<< "sometitle

tomorrow


."
  assert_snapshot
}
