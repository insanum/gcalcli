{
  description = "gcalcli development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # Python dependencies
        pythonPackages = pkgs.python3Packages;

        # Define gcalcli package
        gcalcli = pythonPackages.buildPythonApplication {
          pname = "gcalcli";
          version = "4.5.1"; # Placeholder, dynamic versioning preferred but simple for now
          pyproject = true;

          src = ./.;

          nativeBuildInputs = [
            pythonPackages.setuptools
            pythonPackages.setuptools-scm
            pythonPackages.wheel
          ];

          propagatedBuildInputs = with pythonPackages; [
            argcomplete
            babel
            google-api-python-client
            google-auth-oauthlib
            httplib2
            parsedatetime
            platformdirs
            pydantic
            python-dateutil
            tomli
            truststore
            vobject # Optional dependency included for completeness
          ];

          # Disable tests in the build for now to keep it fast,
          # can enable properly once environment is stable
          doCheck = false;
        };

      in
      {
        packages.default = gcalcli;
        packages.gcalcli = gcalcli;

        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.python3
            pkgs.poetry # In case we migrate later, or for general use

            # Dependencies for running tests
            pythonPackages.google-api-python-client
            pythonPackages.google-auth-oauthlib
            pythonPackages.python-dateutil
            pythonPackages.parsedatetime
            pythonPackages.httplib2
            pythonPackages.argcomplete
            pythonPackages.vobject
            pythonPackages.platformdirs
            pythonPackages.tomli
            pythonPackages.pydantic
            pythonPackages.babel
            pythonPackages.truststore
            pythonPackages.pytest

            # Dev tools
            pythonPackages.ruff
            pythonPackages.mypy
            pythonPackages.tox

            # Build tools
            pythonPackages.setuptools
            pythonPackages.setuptools-scm
          ];

          # Environment variables
          shellHook = ''
            echo "Welcome to the gcalcli development environment!"
            echo "Python version: $(python --version)"
          '';
        };
      }
    );
}
