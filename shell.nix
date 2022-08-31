{ pkgs ? import <nixpkgs> { } }:

let
  python39WithPackages =
    (pkgs.python39.withPackages (pythonPackages: with pythonPackages; [ tox ]));
in pkgs.mkShell { buildInputs = [ python39WithPackages ]; }
