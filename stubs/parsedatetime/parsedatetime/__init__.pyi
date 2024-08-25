import datetime
import logging
import time
from _typeshed import Incomplete
from collections.abc import Generator
from typing import Tuple

__version__: str
__url__: str
__download_url__: str
__description__: str

class NullHandler(logging.Handler):
    def emit(self, record) -> None: ...

log: Incomplete
debug: bool
pdtLocales: Incomplete
VERSION_FLAG_STYLE: int
VERSION_CONTEXT_STYLE: int

class Calendar:
    ptc: Incomplete
    version: Incomplete
    def __init__(self, constants: Incomplete | None = None, version=...) -> None: ...
    def context(self) -> Generator[Incomplete, None, None]: ...
    @property
    def currentContext(self): ...
    def parseDate(self, dateString, sourceTime: Incomplete | None = None): ...
    def parseDateText(self, dateString, sourceTime: Incomplete | None = None): ...
    def evalRanges(self, datetimeString, sourceTime: Incomplete | None = None): ...
    def parseDT(self, datetimeString, sourceTime: Incomplete | None = None, tzinfo: Incomplete | None = None, version: Incomplete | None = None) -> Tuple[datetime.datetime, Incomplete]: ...
    def parse(self, datetimeString, sourceTime: Incomplete | None = None, version: Incomplete | None = None) -> Tuple[time.struct_time, Incomplete]: ...
    def inc(self, source, month: Incomplete | None = None, year: Incomplete | None = None): ...
    def nlp(self, inputString, sourceTime: Incomplete | None = None, version: Incomplete | None = None): ...

class Constants:
    localeID: Incomplete
    fallbackLocales: Incomplete
    locale: Incomplete
    usePyICU: Incomplete
    Second: int
    Minute: int
    Hour: int
    Day: int
    Week: int
    Month: int
    Year: int
    rangeSep: str
    BirthdayEpoch: int
    StartTimeFromSourceTime: bool
    StartHour: int
    YearParseStyle: int
    DOWParseStyle: int
    CurrentDOWParseStyle: bool
    RE_DATE4: Incomplete
    RE_DATE3: Incomplete
    RE_MONTH: Incomplete
    RE_WEEKDAY: Incomplete
    RE_NUMBER: Incomplete
    RE_SPECIAL: Incomplete
    RE_UNITS_ONLY: Incomplete
    RE_UNITS: Incomplete
    RE_QUNITS: Incomplete
    RE_MODIFIER: Incomplete
    RE_TIMEHMS: Incomplete
    RE_TIMEHMS2: Incomplete
    RE_NLP_PREFIX: str
    RE_DATE: Incomplete
    RE_DATE2: Incomplete
    RE_DAY: Incomplete
    RE_DAY2: Incomplete
    RE_TIME: Incomplete
    RE_REMAINING: str
    RE_RTIMEHMS: Incomplete
    RE_RTIMEHMS2: Incomplete
    RE_RDATE: Incomplete
    RE_RDATE3: Incomplete
    DATERNG1: Incomplete
    DATERNG2: Incomplete
    DATERNG3: Incomplete
    TIMERNG1: Incomplete
    TIMERNG2: Incomplete
    TIMERNG3: Incomplete
    TIMERNG4: Incomplete
    re_option: Incomplete
    cre_source: Incomplete
    cre_keys: Incomplete
    def __init__(self, localeID: Incomplete | None = None, usePyICU: bool = True, fallbackLocales=['en_US']) -> None: ...
    def __getattr__(self, name): ...
    def daysInMonth(self, month, year): ...
    def getSource(self, sourceKey, sourceTime: Incomplete | None = None): ...
