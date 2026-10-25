"""Reads and writes whole matches: the only place, with db.queries, that knows the SQL,
the players array encoding (maybe suffix, NULL when empty) and the teams JSON."""

import json
from typing import Any

from psycopg import sql

from conf.conf import table_name
from db.connection import connection
from db.queries import update_teams_on_db
from domain import Match, Participant, Teams
from utils.constants import maybe_placeholder

_COLUMNS = (
    "players, day, time, target, custom_message, pitch, teams, bot_last_message_id"
)


def _decode_participant(raw: str) -> Participant:
    if raw.endswith(maybe_placeholder):
        return Participant(raw[: -len(maybe_placeholder)], is_maybe=True)
    return Participant(raw)


def _encode_participant(participant: Participant) -> str:
    return participant.name + (maybe_placeholder if participant.is_maybe else "")


def _decode_teams(raw: dict[str, list[str]] | None) -> Teams | None:
    if raw is None:
        return None
    return Teams(black=tuple(raw["black"]), white=tuple(raw["white"]))


def _row_to_match(chat_id: int | str, row: tuple[Any, ...]) -> Match:
    """Decode a row selected with _COLUMNS; NULL players decode to an empty list."""
    players, day, time, target, description, pitch, teams, summary_message_id = row
    return Match(
        chat_id=int(chat_id),
        participants=[_decode_participant(raw) for raw in players or []],
        day=day,
        time=time,
        target=target,
        description=description,
        pitch=pitch,
        summary_message_id=summary_message_id,
        teams=_decode_teams(teams),
    )


def get_match(chat_id: int | str) -> Match | None:
    """The match of a chat, or None when /start has not been used (or after /stop)."""
    with connection() as conn:
        cur = conn.execute(
            sql.SQL("SELECT {columns} FROM {table} WHERE chat_id=%s").format(
                columns=sql.SQL(_COLUMNS), table=sql.Identifier(table_name)
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
            ).format(table=sql.Identifier(table_name)),
            [
                str(match.chat_id),
                players,
                match.day,
                match.time,
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
            sql.SQL("DELETE FROM {table} WHERE chat_id=%s").format(
                table=sql.Identifier(table_name)
            ),
            [str(chat_id)],
        )


def _serialize_teams(teams: Teams | None) -> str | None:
    return None if teams is None else json.dumps(teams.as_dict())


def save_teams(chat_id: int | str, teams: Teams | None) -> None:
    """Persist the teams; None revokes them."""
    update_teams_on_db(chat_id, _serialize_teams(teams))
