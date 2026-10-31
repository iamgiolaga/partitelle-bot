"""Reads and writes matches: the only place that knows the SQL and how a match maps onto
the chat, match and participant tables."""

from datetime import datetime
from typing import Any
from uuid import UUID

from psycopg import Connection, sql

from db.connection import connection
from domain import Match, Participant, Teams
from domain.schedule import TIMEZONE

_ACTIVE_MATCH_OF_CHAT = (
    "SELECT m.match_uuid FROM match m JOIN chat c USING (chat_uuid) "
    "WHERE c.telegram_chat_id = %s AND m.stopped_ts IS NULL"
)


def _find_match_uuid(conn: Connection[Any], chat_id: int | str) -> UUID | None:
    row = conn.execute(_ACTIVE_MATCH_OF_CHAT, [int(chat_id)]).fetchone()
    return None if row is None else row[0]


def _lock_match(conn: Connection[Any], chat_id: int | str) -> UUID:
    """The active match of a chat, locked until the transaction ends: the participants'
    positions are computed from the rows that are there, so writers must take turns."""
    row = conn.execute(
        _ACTIVE_MATCH_OF_CHAT + " FOR UPDATE OF m", [int(chat_id)]
    ).fetchone()
    if row is None:
        raise LookupError(f"no match stored for chat {chat_id}")
    return row[0]  # type: ignore[no-any-return]


def _teams_from(rows: list[tuple[str, str, str | None]]) -> Teams | None:
    """The teams are the participants that have one; rows are already in position order."""
    black = tuple(name for name, _, team in rows if team == "black")
    white = tuple(name for name, _, team in rows if team == "white")
    return Teams(black=black, white=white) if black or white else None


def get_match(chat_id: int | str) -> Match | None:
    """The active match of a chat, or None when /start has not been used (or after /stop)."""
    with connection() as conn, conn.transaction():
        row = conn.execute(
            "SELECT m.match_uuid, m.starts_ts, m.target, m.description, m.pitch, "
            "m.telegram_summary_message_id "
            "FROM match m JOIN chat c USING (chat_uuid) "
            "WHERE c.telegram_chat_id = %s AND m.stopped_ts IS NULL",
            [int(chat_id)],
        ).fetchone()
        if row is None:
            return None
        match_uuid, starts, target, description, pitch, summary_message_id = row
        participants = conn.execute(
            "SELECT display_name, status, team FROM participant "
            "WHERE match_uuid = %s ORDER BY position",
            [match_uuid],
        ).fetchall()
    return Match(
        chat_id=int(chat_id),
        participants=[
            Participant(name, status == "maybe") for name, status, _ in participants
        ],
        starts=starts.astimezone(TIMEZONE),
        target=target,
        description=description,
        pitch=pitch,
        summary_message_id=summary_message_id,
        teams=_teams_from(participants),
    )


def _team_of(teams: Teams | None) -> dict[str, str]:
    """Lowercase name -> colour, the way participant names are matched."""
    if teams is None:
        return {}
    colours = {name.lower(): "black" for name in teams.black}
    colours.update({name.lower(): "white" for name in teams.white})
    return colours


def create_match(match: Match) -> None:
    """Store a new active match. The chat row is created on first use; its setting row is
    not, because a missing one means the chat has not been set up."""
    with connection() as conn, conn.transaction():
        chat_uuid = conn.execute(
            # the no-op update makes RETURNING work for an existing chat as well
            "INSERT INTO chat (telegram_chat_id) VALUES (%s) "
            "ON CONFLICT (telegram_chat_id) DO UPDATE "
            "SET telegram_chat_id = EXCLUDED.telegram_chat_id RETURNING chat_uuid",
            [match.chat_id],
        ).fetchone()
        assert chat_uuid is not None
        row = conn.execute(
            "INSERT INTO match (chat_uuid, starts_ts, target, description, pitch, "
            "telegram_summary_message_id) "
            "VALUES (%(chat)s, %(starts)s, %(target)s, %(description)s, "
            "COALESCE(%(pitch)s, (SELECT default_pitch FROM setting WHERE chat_uuid = %(chat)s)), "
            "%(summary)s) RETURNING match_uuid",
            {
                "chat": chat_uuid[0],
                "starts": match.starts,
                "target": match.target,
                "description": match.description,
                "pitch": match.pitch,
                "summary": match.summary_message_id,
            },
        ).fetchone()
        assert row is not None
        colours = _team_of(match.teams)
        for position, participant in enumerate(match.participants, start=1):
            _validate_new_participant(participant)
            conn.execute(
                "INSERT INTO participant (match_uuid, display_name, status, position, team) "
                "VALUES (%s, %s, %s::participant_status, %s, %s::team_colour)",
                [
                    row[0],
                    participant.name,
                    "maybe" if participant.is_maybe else "confirmed",
                    position,
                    None
                    if participant.is_maybe
                    else colours.get(participant.name.lower()),
                ],
            )


def delete_match(chat_id: int | str) -> None:
    """/stop: the match is kept as history, it just stops being the active one."""
    with connection() as conn:
        conn.execute(
            "UPDATE match SET stopped_ts = now() WHERE stopped_ts IS NULL AND chat_uuid = "
            "(SELECT chat_uuid FROM chat WHERE telegram_chat_id = %s)",
            [int(chat_id)],
        )


def save_teams(chat_id: int | str, teams: Teams | None) -> None:
    """Persist the teams; None revokes them."""
    with connection() as conn, conn.transaction():
        match_uuid = _lock_match(conn, chat_id)
        conn.execute(
            "UPDATE participant SET team = NULL WHERE match_uuid = %s", [match_uuid]
        )
        for name, colour in _team_of(teams).items():
            updated = conn.execute(
                "UPDATE participant SET team = %s::team_colour "
                "WHERE match_uuid = %s AND lower(display_name) = %s "
                "AND status = 'confirmed'",
                [colour, match_uuid, name],
            ).rowcount
            if updated != 1:
                raise ValueError(f"{name!r} is not a confirmed participant")


def _set_column(chat_id: int | str, column: str, value: Any) -> None:
    with connection() as conn:
        conn.execute(
            sql.SQL(
                "UPDATE match SET {column} = %s WHERE stopped_ts IS NULL AND chat_uuid = "
                "(SELECT chat_uuid FROM chat WHERE telegram_chat_id = %s)"
            ).format(column=sql.Identifier(column)),
            [value, int(chat_id)],
        )


def set_target(chat_id: int | str, target: int) -> None:
    _set_column(chat_id, "target", target)


def set_starts(chat_id: int | str, starts: datetime) -> None:
    _set_column(chat_id, "starts_ts", starts)


def set_description(chat_id: int | str, description: str) -> None:
    _set_column(chat_id, "description", description)


def set_pitch(chat_id: int | str, pitch: str) -> None:
    _set_column(chat_id, "pitch", pitch)


def set_summary_message_id(chat_id: int | str, message_id: int) -> None:
    _set_column(chat_id, "telegram_summary_message_id", message_id)


def _validate_new_participant(participant: Participant) -> None:
    # a /command is never a name, and an empty name identifies nobody
    if not participant.name.strip() or participant.name.startswith("/"):
        raise ValueError("invalid player name: " + repr(participant.name))


def add_participant(chat_id: int | str, participant: Participant) -> None:
    """Append at the end of the list."""
    _validate_new_participant(participant)
    with connection() as conn, conn.transaction():
        match_uuid = _lock_match(conn, chat_id)
        conn.execute(
            "INSERT INTO participant (match_uuid, display_name, status, position) "
            "SELECT %(match)s, %(name)s, %(status)s::participant_status, "
            "COALESCE(max(position), 0) + 1 FROM participant WHERE match_uuid = %(match)s",
            {
                "match": match_uuid,
                "name": participant.name,
                "status": "maybe" if participant.is_maybe else "confirmed",
            },
        )


def remove_participant(chat_id: int | str, participant: Participant) -> None:
    """Raises ValueError when the participant is not in the list."""
    with connection() as conn, conn.transaction():
        match_uuid = _lock_match(conn, chat_id)
        removed = conn.execute(
            "DELETE FROM participant WHERE match_uuid = %s "
            "AND lower(display_name) = %s AND status = %s::participant_status",
            [
                match_uuid,
                participant.name.lower(),
                "maybe" if participant.is_maybe else "confirmed",
            ],
        ).rowcount
        if removed != 1:
            raise ValueError(f"{participant.name!r} is not in the list")


def set_participant_maybe(chat_id: int | str, name: str, is_maybe: bool) -> None:
    """Flip a participant between confirmed and maybe; the player moves to the end of
    the list, as it joins the new state, and leaves its team (only confirmed players
    can be in one)."""
    with connection() as conn, conn.transaction():
        match_uuid = _lock_match(conn, chat_id)
        updated = conn.execute(
            "UPDATE participant SET status = %(new)s::participant_status, team = NULL, "
            "position = (SELECT COALESCE(max(position), 0) + 1 FROM participant "
            "WHERE match_uuid = %(match)s) "
            "WHERE match_uuid = %(match)s AND lower(display_name) = %(name)s "
            "AND status = %(old)s::participant_status",
            {
                "match": match_uuid,
                "name": name.lower(),
                "new": "maybe" if is_maybe else "confirmed",
                "old": "confirmed" if is_maybe else "maybe",
            },
        ).rowcount
        if updated != 1:
            raise ValueError(f"{name!r} is not in the list")
