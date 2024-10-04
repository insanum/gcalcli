"""Helpers and data objects for gcalcli configuration."""

import argparse
from collections import OrderedDict
from enum import Enum
import sys
from typing import Any, List, Mapping, Optional

if sys.version_info[:2] < (3, 11):
    import tomli as tomllib
else:
    import tomllib

from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import GenerateJsonSchema


class AuthSection(BaseModel):
    """Configuration for settings like client-id used in auth flow.

    Note that client-secret can't be configured here and should be passed on
    command-line instead for security reasons.
    """

    model_config = ConfigDict(title='Settings for authentication')

    client_id: Optional[str] = Field(
        alias='client-id',
        title='Client ID for Google auth token',
        description="""Google client ID for your auth client project.\n
Details: https://github.com/insanum/gcalcli/blob/HEAD/docs/api-auth.md""",
        default=None,
    )


class CalendarsSection(BaseModel):
    model_config = ConfigDict(
        title='Settings about the set of calendars gcalcli operates on'
    )

    default_calendars: List[str] = Field(
        alias='default-calendars',
        title='Calendars to use as default for certain commands when no \
explicit target calendar is otherwise specified',
        default_factory=list,
    )

    ignore_calendars: List[str] = Field(
        alias='ignore-calendars',
        title='Calendars to ignore by default (unless explicitly included \
using --calendar) when running commands against all calendars',
        default_factory=list,
    )


class WeekStart(str, Enum):
    SUNDAY = "sunday"
    MONDAY = "monday"


class OutputSection(BaseModel):
    model_config = ConfigDict(
        title='Settings about gcalcli output (formatting, colors, etc)'
    )

    week_start: WeekStart = Field(
        alias='week-start',
        title='Weekday to treat as start of week',
        default=WeekStart.SUNDAY,
    )


class Config(BaseModel):
    """User configuration for gcalcli command-line tool.

    See https://pypi.org/project/gcalcli/.
    """

    model_config = ConfigDict(
        title='gcalcli config',
        json_schema_extra={'$schema': GenerateJsonSchema.schema_dialect},
    )

    auth: AuthSection = Field(default_factory=AuthSection)
    calendars: CalendarsSection = Field(default_factory=CalendarsSection)
    output: OutputSection = Field(default_factory=OutputSection)

    @classmethod
    def from_toml(cls, config_file):
        config = tomllib.load(config_file)
        return cls(**config)

    def to_argparse_namespace(self) -> argparse.Namespace:
        kwargs = {}
        if self.auth:
            kwargs.update(vars(self.auth))
        if self.calendars:
            kwargs.update(vars(self.calendars))
        if self.output:
            kwargs.update(vars(self.output))
        return argparse.Namespace(**kwargs)

    @classmethod
    def json_schema(cls) -> Mapping[str, Any]:
        schema = super().model_json_schema()
        return schema_entity_ordered(schema)


def schema_entity_ordered(entity: Mapping[str, Any]) -> Mapping[str, Any]:
    """A copy of JSON schema data reordered into more tidy logical ordering."""
    ordered = OrderedDict()
    keys = set(entity.keys())
    for k in ('$schema', 'title', 'description', 'type', 'items'):
        if k in keys:
            keys.remove(k)
            ordered[k] = entity[k]
    if '$defs' in keys:
        keys.remove('$defs')
        ordered['$defs'] = OrderedDict(
            (k, schema_entity_ordered(v)) for k, v in entity['$defs'].items()
        )
    if 'properties' in keys:
        keys.remove('properties')
        ordered['properties'] = OrderedDict(
            (k, schema_entity_ordered(v))
            for k, v in entity['properties'].items()
        )
    # Include remaining fields in arbitrary order.
    for k in sorted(keys):
        ordered[k] = entity[k]
    return ordered
