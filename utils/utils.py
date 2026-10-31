from datetime import datetime
from telegram import Update
from telegram.helpers import escape_markdown
from domain import Match, Teams
from domain.schedule import format_day, format_time
import random


def compute_seconds_from_now(destination_date):
    return destination_date.timestamp() - datetime.now().timestamp()


def get_sender_name(source: Update) -> str | None:
    """Player name of the sender: the lowercase username, or the display name for users
    without a username (not unique and mutable: a telegram user id is the real identity).
    None when the message has no sender (issue #25)."""
    user = source.message.from_user
    if user is None:
        return None
    if user.username:
        return user.username.lower()
    return " ".join(part for part in (user.first_name, user.last_name) if part)


def get_sender_mention(source: Update) -> str | None:
    """How the sender is addressed and stored: `@username`, or the bare display name
    when there is no username (there is no handle to mention). None when the message
    has no sender (issue #25)."""
    user = source.message.from_user
    if user is None:
        return None
    if user.username:
        return "@" + user.username.lower()
    return get_sender_name(source)


def parse_swap(text):
    """Split "scambia a con b" into ("a", "b"), or None when it is not exactly "scambia <a> con <b>"."""
    names = text.split(None, 1)[1:]
    parts = [part.strip() for part in f" {names[0]} ".split(" con ")] if names else []
    if len(parts) != 2 or not all(parts):
        return None
    return parts[0], parts[1]


def swap_players(teams: Teams, x: str, y: str) -> Teams:
    if not teams.contains(x) or not teams.contains(y):
        raise ValueError("Not allowed to swap a player who is not in the teams")
    if teams.colour_of(x) == teams.colour_of(y):
        raise ValueError("Not allowed to swap two players of the same team")
    # the names as stored, whatever case the user typed
    stored = {member.lower(): member for member in teams.members}
    x, y = stored[x.lower()], stored[y.lower()]

    def exchange(team: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(y if p == x else x if p == y else p for p in team)

    return Teams(black=exchange(teams.black), white=exchange(teams.white))


def generate_teams(names: list[str]) -> Teams:
    black_team = random.sample(names, int(len(names) / 2))
    white_team = [name for name in names if name not in black_team]
    return Teams(black=tuple(black_team), white=tuple(white_team))


def flatten_args(args):
    return " ".join(map(str, args))


def parse_names(text):
    """Split "a, b,,c" into ["a", "b", "c"]: comma separated, trimmed, without empty names."""
    return [name.strip() for name in text.split(",") if name.strip()]


def join_names(names):
    """Italian-style list: "a", "a e b", "a, b e c"."""
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " e " + names[-1]


def is_command_name(name):
    """A name that looks like a /command is not a name."""
    return name.startswith("/")


def already_in_message(match: Match) -> str:
    message = "Siete già in " + str(match.target)
    if match.maybe_count:
        message += " (" + str(match.maybe_count) + " in forse)"
    return message


def format_teams(teams: Teams) -> str:
    if not teams.members:
        raise Exception("Teams are empty")

    teams_message = "*SQUADRA NERA* \n"
    for player in teams.black:
        teams_message = teams_message + " - " + escape_markdown(player) + "\n"

    teams_message = teams_message + "\n"
    teams_message = teams_message + "*SQUADRA BIANCA* \n"
    for player in teams.white:
        teams_message = teams_message + " - " + escape_markdown(player) + "\n"

    return teams_message


def format_summary(match: Match) -> str:
    pitch = match.pitch
    if pitch is None:
        pitch = "Usa il comando /setpitch <campo> per inserire la struttura sportiva dove giocherete."

    prefix = (
        f"*GIORNO*: {escape_markdown(format_day(match.starts))} | "
        f"{format_time(match.starts)}\n\n"
    )
    # the description is deliberately not escaped: users format it with markdown
    appendix = f"{match.description}\n\n*CAMPO*: \n{escape_markdown(pitch)}"

    player_list = ""
    for i in range(match.target):
        if i < len(match.participants):
            participant = match.participants[i]
            icon = "❓" if participant.is_maybe else "✅"
            player_list += f"{i + 1}. {escape_markdown(participant.name)} {icon}\n"
        else:
            player_list += f"{i + 1}. ❌\n"

    return prefix + player_list + "\n" + appendix
