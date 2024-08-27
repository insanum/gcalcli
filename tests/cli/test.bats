setup() {
  load 'test_helper/bats-support/load'
  load 'test_helper/bats-assert/load'
}

@test "can run" {
  run gcalcli
  assert_output --regexp 'usage: .*error:.*required: .*command'
}

@test "prints correct help" {
  run gcalcli -h
  assert_output --regexp 'positional arguments:.*list.*search.*edit.*options:'
}
