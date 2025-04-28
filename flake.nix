{
  description = "gcalcli";
  inputs = { nixpkgs = { url = "nixpkgs/nixos-22.05"; }; };
  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
    in { devShells.${system}.default = import ./shell.nix { inherit pkgs; }; };
}
