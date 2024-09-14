"""Helpers and data objects for gcalcli configuration."""

import argparse
from collections import OrderedDict
import sys
from typing import Any, List, Mapping

if sys.version_info[:2] < (3, 11):
    import toml as tomllib
else:
    import tomllib

from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import GenerateJsonSchema


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


class Config(BaseModel):
    """User configuration for gcalcli command-line tool.

    See https://pypi.org/project/gcalcli/.
    """

    model_config = ConfigDict(
        title='gcalcli config',
        json_schema_extra={'$schema': GenerateJsonSchema.schema_dialect},
    )

    calendars: CalendarsSection = Field(default_factory=CalendarsSection)

    @classmethod
    def from_toml(cls, config_file):
        config = tomllib.load(config_file)
        return cls(**config)

    def to_argparse_namespace(self) -> argparse.Namespace:
        return argparse.Namespace(**vars(self.calendars or {}))

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
