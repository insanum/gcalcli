{ pkgs ? import <nixpkgs> { } }:

let
  python38WithPackages =
    (pkgs.python38.withPackages (pythonPackages: with pythonPackages; [ tox ]));
in pkgs.mkShell { buildInputs = [ python38WithPackages ]; }
