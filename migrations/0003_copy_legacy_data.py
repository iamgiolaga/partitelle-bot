"""Copy the legacy all_players rows into the normalized schema (chat, setting, match, participant).

Self-contained on purpose: no import from the application (utils, domain, db, conf). Every fresh schema
replays all the migrations, so this file must keep working unchanged when those modules are rewritten.
The parsing rules and constants below are therefore a frozen copy of what the bot did at cutover time.

all_players is left untouched. Only chat_id is ever printed: names and texts are personal data.
"""

import re
import unicodedata
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from dateutil.parser import parse
from yoyo import step

__depends__ = {"0002_schema_redesign"}

TIMEZONE = ZoneInfo("Europe/Rome")
DEFAULT_TIME = time(20, 0)
DEFAULT_TARGET = 10
MIN_TARGET, MAX_TARGET = 2, 40
WEDNESDAY = 2  # date.weekday(): 0 = Monday

# marks a "maybe" participant inside the legacy players array
MAYBE_SUFFIX = "%is%maybe%present"

# the pitch the /bamboo command started every match with
BAMBOO_PITCH = (
    "Crespi Sport Village \n"
    "\n"
    "Via Carlo Valvassori Peroni, 48, 20133 \n"
    "Milano, MI, 02 266 3774 \n"
    "https://g.co/kgs/L9b6KZ"
)

# dateutil does not know the Italian weekdays: a leading one is dropped, but only when a date follows
ITALIAN_WEEKDAY = re.compile(
    r"^\s*(luned[iì]|marted[iì]|mercoled[iì]|gioved[iì]|venerd[iì]|sabato|domenica)"
    r"\s+(?=\d{1,2}[/.-]\d{1,2})",
    re.IGNORECASE,
)
WEEKDAY_ONLY = re.compile(
    r"\s*(luned[iì]|marted[iì]|mercoled[iì]|gioved[iì]|venerd[iì]|sabato|domenica)\s*",
    re.IGNORECASE,
)
WEEKDAY_NUMBER = {
    "lunedi": 0,
    "martedi": 1,
    "mercoledi": 2,
    "giovedi": 3,
    "venerdi": 4,
    "sabato": 5,
    "domenica": 6,
}


def extract_day(text: str) -> date | None:
    """The date written in the day column, or None when dateutil cannot read it."""
    try:
        return parse(ITALIAN_WEEKDAY.sub("", text), dayfirst=True).date()
    except (ValueError, OverflowError):
        return None


def next_weekday(today: date, weekday: int) -> date:
    """The first date with that weekday strictly after today."""
    return today + timedelta(days=(weekday - today.weekday()) % 7 or 7)


def resolve_day(text: str | None, today: date) -> tuple[date, str | None]:
    """The match date and, when it is a guess, the kind of fallback used."""
    text = text or ""
    found = extract_day(text)
    if found is not None:
        return found, None
    only = WEEKDAY_ONLY.fullmatch(text)
    if only is not None:
        name = unicodedata.normalize("NFD", only.group(1).lower())
        name = name.replace(chr(0x300), "")  # drop the grave accent
        return next_weekday(today, WEEKDAY_NUMBER[name]), "weekday-only day"
    return next_weekday(today, WEDNESDAY), "unreadable day"


def resolve_time(text: str | None) -> tuple[time, str | None]:
    """The match time and, when it is a guess, the kind of fallback used.
    Accepted: H:MM, HH:MM, H.MM, HH.MM, or a bare hour."""
    found = re.fullmatch(r"(\d{1,2})(?:[:.](\d{2}))?", (text or "").strip())
    if found is not None:
        hours, minutes = int(found.group(1)), int(found.group(2) or 0)
        if hours <= 23 and minutes <= 59:
            return time(hours, minutes), None
    return DEFAULT_TIME, "unreadable time"


def resolve_starts(
    day: str | None, at: str | None, today: date
) -> tuple[datetime, list[str]]:
    """The start of a legacy match (Europe/Rome) and the fallbacks it needed."""
    match_day, day_fallback = resolve_day(day, today)
    match_time, time_fallback = resolve_time(at)
    fallbacks = [fb for fb in (day_fallback, time_fallback) if fb]
    return datetime.combine(match_day, match_time, tzinfo=TIMEZONE), fallbacks


def decode_players(players: list[str] | None) -> tuple[list[tuple[str, str]], int]:
    """(name, status) in array order, skipping empty names and case-insensitive
    duplicates (the first wins); also the number of duplicates skipped."""
    decoded: list[tuple[str, str]] = []
    seen: set[str] = set()
    duplicates = 0
    for raw in players or []:
        status = "maybe" if raw.endswith(MAYBE_SUFFIX) else "confirmed"
        name = raw[: -len(MAYBE_SUFFIX)] if status == "maybe" else raw
        if not name.strip():
            continue
        if name.lower() in seen:
            duplicates += 1
            continue
        seen.add(name.lower())
        decoded.append((name, status))
    return decoded, duplicates


def team_of(teams: object) -> dict[str, str]:
    """Lowercase name -> colour from the legacy teams JSON."""
    if not isinstance(teams, dict):
        return {}
    colours: dict[str, str] = {}
    for colour in ("black", "white"):
        names = teams.get(colour)
        for name in names if isinstance(names, list) else []:
            if isinstance(name, str):
                colours.setdefault(name.lower(), colour)
    return colours


def copy_legacy_rows(conn, today: date) -> None:
    cur = conn.cursor()
    cur.execute(
        "SELECT chat_id, players, day, time, target, custom_message, pitch, "
        "bot_last_message_id, teams FROM all_players ORDER BY chat_id"
    )
    rows = cur.fetchall()
    stopped = reminded = 0

    for (
        chat_id,
        players,
        day,
        at,
        target,
        description,
        pitch,
        summary_message_id,
        teams,
    ) in rows:
        cur.execute(
            "INSERT INTO chat (telegram_chat_id) VALUES (%s) RETURNING chat_uuid",
            [chat_id],
        )
        chat_uuid = cur.fetchone()[0]
        starts, fallbacks = resolve_starts(day, at, today)
        for fallback in fallbacks:
            print(f"0003 chat {chat_id}: {fallback}, fallback used")
        if target is None:
            target = DEFAULT_TARGET
        elif not MIN_TARGET <= target <= MAX_TARGET:
            print(f"0003 chat {chat_id}: target out of range, default used")
            target = DEFAULT_TARGET

        # stale chats are stopped, and a match already played gets no late reminder
        cur.execute(
            "INSERT INTO match (chat_uuid, starts_ts, target, description, pitch, "
            "telegram_summary_message_id, stopped_ts, reminder_sent_ts) "
            "VALUES (%(chat)s, %(starts)s, %(target)s, %(description)s, %(pitch)s, %(summary)s, "
            "CASE WHEN %(starts)s < now() - interval '1 month' THEN now() END, "
            "CASE WHEN %(starts)s + interval '2 hours' <= now() THEN now() END) "
            "RETURNING match_uuid, stopped_ts IS NOT NULL, reminder_sent_ts IS NOT NULL",
            {
                "chat": chat_uuid,
                "starts": starts,
                "target": target,
                "description": description,
                "pitch": pitch,
                "summary": summary_message_id,
            },
        )
        match_uuid, is_stopped, is_reminded = cur.fetchone()
        stopped += is_stopped
        reminded += is_reminded

        # the default pitch is only kept for chats still using the bot: a stopped
        # match means the chat is dormant, so its old pitch is not worth carrying over
        cur.execute(
            "INSERT INTO setting (chat_uuid, default_pitch) VALUES (%s, %s)",
            [
                chat_uuid,
                BAMBOO_PITCH if pitch == BAMBOO_PITCH and not is_stopped else None,
            ],
        )

        participants, duplicates = decode_players(players)
        if duplicates:
            print(f"0003 chat {chat_id}: {duplicates} duplicate name(s) skipped")
        colours = team_of(teams)
        confirmed = {
            name.lower() for name, status in participants if status == "confirmed"
        }
        unmatched = len(colours.keys() - confirmed)
        if unmatched:
            print(
                f"0003 chat {chat_id}: {unmatched} team name(s) matched no confirmed player"
            )
        for position, (name, status) in enumerate(participants, start=1):
            cur.execute(
                "INSERT INTO participant (match_uuid, display_name, status, position, team) "
                "VALUES (%s, %s, %s::participant_status, %s, %s::team_colour)",
                [
                    match_uuid,
                    name,
                    status,
                    position,
                    colours.get(name.lower()) if status == "confirmed" else None,
                ],
            )

    if rows:
        print(
            f"0003 copied {len(rows)} chat(s): {stopped} match(es) stopped, "
            f"{reminded} reminder(s) marked as sent"
        )


def apply_copy(conn):
    copy_legacy_rows(conn, datetime.now(TIMEZONE).date())


step(apply_copy)
