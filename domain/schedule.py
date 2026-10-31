"""When a match starts: the defaults, the Italian rendering and the reading of what users write.

Free of Telegram and storage concerns, so the bot and the repository share one set of rules.
"""

import re
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from dateutil.parser import parse

from utils.constants import default_time

TIMEZONE = ZoneInfo("Europe/Rome")
DEFAULT_TIME = time.fromisoformat(default_time)
WEDNESDAY = 2  # date.weekday(): 0 = Monday

# an explicit mapping: the locale module depends on what the host has installed
WEEKDAY_NAMES = (
    "Lunedì",
    "Martedì",
    "Mercoledì",
    "Giovedì",
    "Venerdì",
    "Sabato",
    "Domenica",
)

_WEEKDAY_PATTERN = (
    "luned[iì]|marted[iì]|mercoled[iì]|gioved[iì]|venerd[iì]|sabato|domenica"
)

# dateutil does not know the Italian weekdays: a leading one is dropped, but only when a date follows
_LEADING_WEEKDAY = re.compile(
    rf"^\s*(?:{_WEEKDAY_PATTERN})\s+(?=\d{{1,2}}[/.-]\d{{1,2}})", re.IGNORECASE
)
_TIME = re.compile(r"(\d{1,2})(?:[:.](\d{2}))?")


def next_weekday(today: date, weekday: int) -> date:
    """The first date with that weekday strictly after today."""
    return today + timedelta(days=(weekday - today.weekday()) % 7 or 7)


def next_start(now: datetime | None = None) -> datetime:
    """The next default weekday at the default time: today itself while that moment is still ahead."""
    now = now.astimezone(TIMEZONE) if now else datetime.now(TIMEZONE)
    if now.weekday() == WEDNESDAY and now.time() < DEFAULT_TIME:
        day = now.date()
    else:
        day = next_weekday(now.date(), WEDNESDAY)
    return datetime.combine(day, DEFAULT_TIME, tzinfo=TIMEZONE)


def format_day(starts: datetime) -> str:
    """The canonical day, e.g. "Mercoledì 04/11/2026"."""
    return f"{WEEKDAY_NAMES[starts.weekday()]} {starts:%d/%m/%Y}"


def format_time(starts: datetime) -> str:
    return f"{starts:%H:%M}"


def parse_day(text: str) -> date | None:
    """The date written by a user (day first), or None when it cannot be read."""
    try:
        parsed: datetime = parse(_LEADING_WEEKDAY.sub("", text), dayfirst=True)
    except (ValueError, OverflowError):
        return None
    return parsed.date()


def parse_time(text: str) -> time | None:
    """H:MM, HH:MM, H.MM, HH.MM or a bare hour (e.g. "20" is 20:00); None when invalid."""
    found = _TIME.fullmatch(text.strip())
    if found is None:
        return None
    hours, minutes = int(found.group(1)), int(found.group(2) or 0)
    if hours > 23 or minutes > 59:
        return None
    return time(hours, minutes)


def with_day(starts: datetime, day: date) -> datetime:
    return datetime.combine(day, starts.time(), tzinfo=TIMEZONE)


def with_time(starts: datetime, at: time) -> datetime:
    return datetime.combine(starts.date(), at, tzinfo=TIMEZONE)
