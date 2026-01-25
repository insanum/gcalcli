# Automation Guide

`gcalcli` provides features specifically designed for automation scripts and agents.

## Non-Interactive Mode support (CI/CD)

Use automation flags to prevent the tool from pausing for user input:

- `--yes`, `--force`, `--no-prompt`: Automatically answer "yes" to confirmation prompts (like delete).
- `--noprompt` (specific to `add`): Skips prompting for missing fields during event creation.
