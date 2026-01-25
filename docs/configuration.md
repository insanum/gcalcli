# Configuration

`gcalcli` supports configuration via a `config.toml` file, typically located at `~/.config/gcalcli/config.toml` (or `$XDG_CONFIG_HOME/gcalcli/config.toml`).

## Structure

The configuration is divided into sections:

### `[auth]`

Settings for authentication (Client ID).

### `[calendars]`

Settings for default and ignored calendars.

### `[output]`

Settings for output formatting (week start).

### `[default]` (New)

Set default values for global command-line flags.

```toml
[default]
interactive = false  # Disable interactive prompts (simulates --yes)
color = true         # Enable/Disable color
conky = false        # Conky compatible output
```

## Example `config.toml`

```toml
[auth]
client-id = "your-client-id.apps.googleusercontent.com"

[calendars]
default-calendars = ["Work", "Personal"]
ignore-calendars = ["Holidays"]

[output]
week-start = "monday"

[default]
interactive = true
color = true
```
