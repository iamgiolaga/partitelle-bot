"""Reads and writes matches: the only place that knows the SQL, the players array
encoding (maybe suffix, NULL when empty) and the teams JSON."""

import json
from datetime import date, datetime, time
from typing import Any

from psycopg import Connection, sql

from conf.conf import table_name
from db.connection import connection
from domain import Match, Participant, Teams
from domain.schedule import (
    DEFAULT_TIME,
    TIMEZONE,
    WEDNESDAY,
    format_day,
    format_time,
    next_weekday,
    parse_day,
    parse_time,
    weekday_number,
)

# marks a "maybe" participant inside the stored players array
_MAYBE_SUFFIX = "%is%maybe%present"

_COLUMNS = (
    "players, day, time, target, custom_message, pitch, teams, bot_last_message_id"
)


def _decode_participant(raw: str) -> Participant:
    if raw.endswith(_MAYBE_SUFFIX):
        return Participant(raw[: -len(_MAYBE_SUFFIX)], is_maybe=True)
    return Participant(raw)


def _encode_participant(participant: Participant) -> str:
    return participant.name + (_MAYBE_SUFFIX if participant.is_maybe else "")


def _decode_starts(day: str | None, at: str | None, today: date) -> datetime:
    """The start of a stored match. The day and time columns are free text written by older
    versions, so this never fails: what cannot be read falls back to the default."""
    text = day or ""
    match_day = parse_day(text)
    if match_day is None:
        weekday = weekday_number(text)
        match_day = next_weekday(today, WEDNESDAY if weekday is None else weekday)
    match_time: time = parse_time(at or "") or DEFAULT_TIME
    return datetime.combine(match_day, match_time, tzinfo=TIMEZONE)


def _decode_teams(raw: dict[str, list[str]] | None) -> Teams | None:
    if raw is None:
        return None
    return Teams(black=tuple(raw["black"]), white=tuple(raw["white"]))


def _row_to_match(chat_id: int | str, row: tuple[Any, ...]) -> Match:
    """Decode a row selected with _COLUMNS; NULL players decode to an empty list."""
    players, day, at, target, description, pitch, teams, summary_message_id = row
    return Match(
        chat_id=int(chat_id),
        participants=[_decode_participant(raw) for raw in players or []],
        starts=_decode_starts(day, at, datetime.now(TIMEZONE).date()),
        target=target,
        description=description,
        pitch=pitch,
        summary_message_id=summary_message_id,
        teams=_decode_teams(teams),
    )


def _table() -> sql.Identifier:
    if table_name is None:
        raise RuntimeError("PB_DB_TABLE_NAME is not set")
    return sql.Identifier(table_name)


def get_match(chat_id: int | str) -> Match | None:
    """The match of a chat, or None when /start has not been used (or after /stop)."""
    with connection() as conn:
        cur = conn.execute(
            sql.SQL("SELECT {columns} FROM {table} WHERE chat_id=%s").format(
                columns=sql.SQL(_COLUMNS), table=_table()
            ),
            [str(chat_id)],
        )
        row = cur.fetchone()
    return None if row is None else _row_to_match(chat_id, row)


def create_match(match: Match) -> None:
    players = (
        "{" + ",".join(_encode_participant(p) for p in match.participants) + "}"
        if match.participants
        else None
    )
    with connection() as conn:
        conn.execute(
            sql.SQL(
                "INSERT INTO {table} (chat_id, players, day, time, target, custom_message, pitch, teams, bot_last_message_id) "
                "VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            ).format(table=_table()),
            [
                str(match.chat_id),
                players,
                format_day(match.starts),
                format_time(match.starts),
                str(match.target),
                match.description,
                match.pitch,
                _serialize_teams(match.teams),
                None
                if match.summary_message_id is None
                else str(match.summary_message_id),
            ],
        )


def delete_match(chat_id: int | str) -> None:
    with connection() as conn:
        conn.execute(
            sql.SQL("DELETE FROM {table} WHERE chat_id=%s").format(table=_table()),
            [str(chat_id)],
        )


def _serialize_teams(teams: Teams | None) -> str | None:
    return None if teams is None else json.dumps(teams.as_dict())


def save_teams(chat_id: int | str, teams: Teams | None) -> None:
    """Persist the teams; None revokes them."""
    _set_column(chat_id, "teams", _serialize_teams(teams))


def _set_column(chat_id: int | str, column: str, value: str | int | None) -> None:
    with connection() as conn:
        conn.execute(
            sql.SQL("UPDATE {table} SET {column} = %s WHERE chat_id=%s").format(
                table=_table(), column=sql.Identifier(column)
            ),
            [value, str(chat_id)],
        )


def set_target(chat_id: int | str, target: int) -> None:
    _set_column(chat_id, "target", str(target))


def set_starts(chat_id: int | str, starts: datetime) -> None:
    with connection() as conn:
        conn.execute(
            sql.SQL("UPDATE {table} SET day = %s, time = %s WHERE chat_id=%s").format(
                table=_table()
            ),
            [format_day(starts), format_time(starts), str(chat_id)],
        )


def set_description(chat_id: int | str, description: str) -> None:
    _set_column(chat_id, "custom_message", description)


def set_pitch(chat_id: int | str, pitch: str) -> None:
    _set_column(chat_id, "pitch", pitch)


def set_summary_message_id(chat_id: int | str, message_id: int) -> None:
    _set_column(chat_id, "bot_last_message_id", str(message_id))


def _validate_new_participant(participant: Participant) -> None:
    # a /command is never a name, and an empty name would corrupt the stored array
    entry = _encode_participant(participant)
    if not entry.replace(_MAYBE_SUFFIX, "").strip() or entry.startswith("/"):
        raise ValueError("invalid player name: " + repr(entry))


def _lock_players(conn: Connection[Any], chat_id: int | str) -> list[str]:
    """The stored entries of a chat, with the row locked until the transaction ends."""
    row = conn.execute(
        sql.SQL("SELECT players FROM {table} WHERE chat_id=%s FOR UPDATE").format(
            table=_table()
        ),
        [str(chat_id)],
    ).fetchone()
    if row is None:
        raise LookupError(f"no match stored for chat {chat_id}")
    return list(row[0] or [])


def _store_players(
    conn: Connection[Any], chat_id: int | str, entries: list[str]
) -> None:
    # an empty list is stored as NULL, never as an empty array
    conn.execute(
        sql.SQL("UPDATE {table} SET players = %s WHERE chat_id=%s").format(
            table=_table()
        ),
        [entries or None, str(chat_id)],
    )


def add_participant(chat_id: int | str, participant: Participant) -> None:
    """Append at the end of the list."""
    _validate_new_participant(participant)
    with connection() as conn, conn.transaction():
        entries = _lock_players(conn, chat_id)
        entries.append(_encode_participant(participant))
        _store_players(conn, chat_id, entries)


def remove_participant(chat_id: int | str, participant: Participant) -> None:
    """Raises ValueError when the participant is not in the list."""
    with connection() as conn, conn.transaction():
        entries = _lock_players(conn, chat_id)
        entries.remove(_encode_participant(participant))
        _store_players(conn, chat_id, entries)


def set_participant_maybe(chat_id: int | str, name: str, is_maybe: bool) -> None:
    """Flip a participant between confirmed and maybe; the player moves to the end of
    the list, as it joins the new state."""
    with connection() as conn, conn.transaction():
        entries = _lock_players(conn, chat_id)
        entries.remove(_encode_participant(Participant(name, not is_maybe)))
        entries.append(_encode_participant(Participant(name, is_maybe)))
        _store_players(conn, chat_id, entries)
