from datetime import datetime, timedelta
from dateutil.parser import parse
from telegram import Update
from telegram.helpers import escape_markdown
from domain import Match, Teams
from utils.constants import default_time
import random
import re


def get_next_weekday(startdate: str, weekday: int, now=None, match_time=None) -> str:
    """
    Get the next weekday from a given date
    @param startdate: the starting date
    @param weekday: the weekday to find (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
    @param now: the current moment, needed only together with match_time
    @param match_time: the time (datetime.time) of the match: when startdate is already
    that weekday and now is before it, startdate itself is returned (from the match time on, it is the following week)
    @return: the date of the next specified weekday in the format 'dd/mm/yyyy'

    """
    format = "%d/%m/%Y"
    d = datetime.strptime(startdate, format)
    days_ahead = weekday - d.weekday()
    if days_ahead == 0 and match_time is not None and now.time() < match_time:
        return d.strftime(format)
    if days_ahead <= 0:
        days_ahead += 7
    return (d + timedelta(days_ahead)).strftime(format)


def compute_next_wednesday(time=None):
    """
    @param time: the match time as 'HH:MM'; when it is a valid time and today is Wednesday
    before it, the result is today, otherwise the following Wednesday
    """
    now = datetime.today()
    match_time = extract_match_time(time) if time else -1
    return get_next_weekday(
        now.strftime("%d/%m/%Y"),
        2,
        now,
        None if match_time == -1 else match_time,
    )


ITALIAN_WEEKDAY = re.compile(
    r"^\s*(luned[iì]|marted[iì]|mercoled[iì]|gioved[iì]|venerd[iì]|sabato|domenica)"
    r"\s+(?=\d{1,2}[/.-]\d{1,2})",
    re.IGNORECASE,
)


def extract_match_day(day):
    # dateutil does not know the Italian weekdays (e.g. the default "Mercoledì 28/10/2026"):
    # drop a leading one, but only when a date follows (a weekday alone is still unreadable)
    day = ITALIAN_WEEKDAY.sub("", day)
    try:
        extracted_day = parse(day, dayfirst=True)
    except ValueError:
        extracted_day = -1
    return extracted_day


def extract_match_time(time):
    try:
        extracted_time = datetime.strptime(time, "%H:%M").time()
    except ValueError:
        extracted_time = -1
    return extracted_time


def normalize_match_time(text):
    """
    Validate the time written by a user and return it as 'HH:MM', or None when invalid.
    Accepted: H:MM, HH:MM, H.MM, HH.MM (e.g. '9:30' -> '09:30', '21.30' -> '21:30')
    """
    found = re.fullmatch(r"(\d{1,2})[:.](\d{2})", text.strip())
    if found is None:
        return None
    hours, minutes = int(found.group(1)), int(found.group(2))
    if hours > 23 or minutes > 59:
        return None
    return f"{hours:02d}:{minutes:02d}"


def compute_seconds_from_now(destination_date):
    return destination_date.timestamp() - datetime.now().timestamp()


def get_sender_name(source: Update):
    """Player name of the sender: the lowercase username, or the display name for users
    without a username (not unique and mutable: a telegram user id is the real identity)."""
    user = source.message.from_user
    if user.username:
        return user.username.lower()
    return " ".join(part for part in (user.first_name, user.last_name) if part)


def get_sender_mention(source: Update):
    """How the sender is addressed and stored: `@username`, or the bare display name
    when there is no username (there is no handle to mention)."""
    user = source.message.from_user
    if user.username:
        return "@" + get_sender_name(source)
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
    if (x in teams.black and y in teams.black) or (
        x in teams.white and y in teams.white
    ):
        raise ValueError("Not allowed to swap two players of the same team")

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
        f"*GIORNO*: {escape_markdown(match.day)} | {escape_markdown(match.time)}\n\n"
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


def default_match_day() -> str:
    return "Mercoledì " + compute_next_wednesday(default_time)
