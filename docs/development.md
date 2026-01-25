# Development Setup

This project uses [Nix](https://nixos.org/) to enforce a reproducible development environment.

## Prerequisites

1.  **Install Nix**:

    ```bash
    sh <(curl -L https://nixos.org/nix/install)
    ```

2.  **Enable Flakes** (if not already enabled):
    Add `experimental-features = nix-command flakes` to `/etc/nix/nix.conf`.

3.  **(Recommended) Install direnv**:
    ```bash
    # On macOS with Homebrew
    brew install direnv
    # Hook it into your shell (add to .zshrc or .bashrc):
    eval "$(direnv hook zsh)"
    ```

## Quick Start

1.  **Clone the repo**:

    ```bash
    git clone https://github.com/insanum/gcalcli.git
    cd gcalcli
    ```

2.  **Enter the environment**:
    If you have `direnv`, just `allow` the directory:

    ```bash
    direnv allow
    ```

    Otherwise, drop into the shell manually:

    ```bash
    nix develop
    ```

3.  **Run the tool**:

    ```bash
    # Run from source
    python -m gcalcli.cli list
    ```

4.  **Run tests**:
    ```bash
    tox
    ```

## Build the Package

To build the package exactly as it would be distributed:

```bash
nix build
./result/bin/gcalcli --version
```
