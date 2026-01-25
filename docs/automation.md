# Automation Guide

`gcalcli` provides features specifically designed for automation scripts and agents.

## Structured Output (JSON)

Use the `--json` flag to get machine-readable output. This is supported by:

- `list`
- `agenda`
- `search`
- `updates`

### Calendar List Schema (`list --json`)

Returns a list of Calendar objects:

```json
[
  {
    "id": "user@gmail.com",
    "summary": "Work Calendar",
    "accessRole": "owner",
    "selected": true,
    ...
  }
]
```

### Event Schema (`agenda --json`, `search --json`)

Returns a list of Event objects with ISO 8601 dates:

```json
[
  {
    "id": "event_id_string",
    "summary": "Meeting with Team",
    "description": "Discuss Q1 goals",
    "start": "2023-10-27T14:00:00-07:00",
    "end": "2023-10-27T15:00:00-07:00",
    "allday": false,
    "location": "Conference Room A",
    "htmlLink": "https://calendar.google.com/...",
    "calendar": "Work Calendar",
    "calendar_id": "user@gmail.com",
    "attendees": [{ "email": "boss@example.com", "responseStatus": "accepted" }]
  }
]
```

### Notes on Dates

- **Time Events**: `start` and `end` are full ISO 8601 strings including timezone offset.
- **All Day Events**: `start` and `end` are `YYYY-MM-DD` strings. `allday` will be `true`.
