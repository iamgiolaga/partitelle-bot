from datetime import datetime, timedelta
from dateutil.parser import parse
from telegram.utils.helpers import escape_markdown
from utils.constants import maybe_placeholder
import random
import json



def get_next_weekday(startdate: str, weekday: int) -> str:
    """
    Get the next weekday from a given date
    @param startdate: the starting date
    @param weekday: the weekday to find (0 = Monday, 1 = Tuesday, ..., 6 = Sunday)
    @return: the date of the next specified weekday in the format 'dd/mm/yyyy'

    """
    format = '%d/%m/%Y'
    d = datetime.strptime(startdate, format)
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return (d + timedelta(days_ahead)).strftime(format)

def compute_next_wednesday():
    return get_next_weekday((datetime.today().strftime('%d/%m/%Y')), 2)

def extract_match_day(day):
    try:
        extracted_day = parse(day, dayfirst=True)
    except:
        extracted_day = -1
    return extracted_day

def extract_match_time(time):
    try:
        extracted_time = datetime.strptime(time, '%H:%M').time()
    except:
        extracted_time = -1
    return extracted_time

def compute_seconds_from_now(destination_date):
    return destination_date.timestamp() - datetime.now().timestamp()

def get_sender_name(source):
    return source.message.from_user.username.lower()

def swap_players(teams, x, y):
    error = False

    if (x in teams['black'] and y in teams['black']) or (x in teams['white'] and y in teams['white']):
        error = True

    temp_black = None
    temp_white = None

    if x in teams['black']:
        temp_black = [y if player == x else player for player in teams['black']]
    else:
        temp_white = [y if player == x else player for player in teams['white']]

    if y in teams['black']:
        temp_black = [x if player == y else player for player in teams['black']]
    else:
        temp_white = [x if player == y else player for player in teams['white']]

    teams['black'] = temp_black
    teams['white'] = temp_white

    return error, json.dumps(teams)

def generate_teams(players):
    black_team = random.sample(players, int(len(players)/2))
    white_team = [player for player in players if player not in black_team]
    teams = {
        'black': black_team,
        'white': white_team
    }
    return json.dumps(teams)

def flatten_args(args):
    res = ""

    for index, arg in enumerate(args):
        if index == 0:
            res = str(arg)
        else:
            res = res + " " + str(arg)

    return res

def filter_maybe_placeholders(players):
    return [player for player in players if maybe_placeholder not in player]

def format_teams(teams):
    json_teams = json.loads(teams)
    black_team = json_teams["black"]
    white_team = json_teams["white"]

    teams_message = "*SQUADRA NERA* \n"
    for player in black_team:
        teams_message = teams_message + " - " + escape_markdown(player) + "\n"

    teams_message = teams_message + "\n"
    teams_message = teams_message + "*SQUADRA BIANCA* \n"
    for player in white_team:
        teams_message = teams_message + " - " + escape_markdown(player) + "\n"

    return teams_message

def format_summary(all_players, day, time, target, default_message, pitch):
    player_list = ""

    prefix = "*GIORNO*: " + escape_markdown(day) + " | " + escape_markdown(time) + "\n"\

    if pitch is None:
        pitch = "Usa il comando /setpitch <campo> per inserire la struttura sportiva dove giocherete."

    appendix = default_message + \
                "\n"\
                "*CAMPO*: \n"\
                + escape_markdown(pitch)

    for i in range(0, target):
        if all_players and i < len(all_players):
            player = all_players[i]
            if player.endswith(maybe_placeholder):
                player = player.replace(maybe_placeholder, "")
                presence_outcome_icon = "❓"
            else:
                presence_outcome_icon = "✅"
            player_list = player_list + str(i + 1) + ". " + escape_markdown(player) + " " + presence_outcome_icon + "\n"
        else:
            player_list = player_list + str(i + 1) + ". ❌ \n"

    return prefix + "\n" + player_list + "\n" + appendix
