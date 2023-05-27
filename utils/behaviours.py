from datetime import datetime, timedelta
from dateutil.parser import parse
from utils.macros import maybe_placeholder
from telegram.utils.helpers import escape_markdown
import random
import json

def get_next_weekday(startdate, weekday):
    """
    @startdate: given date
    @weekday: week day as a integer, between 0 (Monday) to 6 (Sunday)
    """
    d = datetime.strptime(startdate, '%d/%m/%Y')
    t = timedelta((7 + weekday - d.weekday()) % 7)
    return (d + t).strftime('%d/%m/%Y')

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

def print_teams(teams, update: Update, context: CallbackContext):
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

    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=teams_message)

def reminder(context):
    job = context.job
    chat_id = job.name

    msg = context.bot.send_message(chat_id, text="Ciao bestie 😎, com'è andata la partita? C'è qualcuno che non ha ancora pagato la sua quota?")

    try:
        context.bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id)
    except:
        print("No admin rights to pin the message")

    update_bot_last_message_id_on_db(chat_id, msg.message_id)

def set_payment_reminder(update, context, day, time):
    chat_id = update.effective_message.chat_id
    match_time = extract_match_time(time)
    reminder_time_from_now = -1

    if match_time == -1:
        match_date = extract_match_day(day)
        waiting_time_in_seconds = 36 * 3600
    else:
        match_date = extract_match_day(f"{day} {time}")
        waiting_time_in_seconds = 2 * 3600

    if match_date != -1:
        reminder_time_from_now = compute_seconds_from_now(match_date) + waiting_time_in_seconds

    if reminder_time_from_now > 0:
        context.job_queue.run_once(reminder, reminder_time_from_now, context=context, name=str(chat_id))

def remove_job_if_exists(name, context):
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True

def beautify(all_players, day, time, target, custom_message, pitch):
    player_list = ""

    prefix = "*GIORNO*: " + escape_markdown(day) + " | " + escape_markdown(time) + "\n"\

    if pitch is None:
        pitch = "Usa il comando /setpitch <campo> per inserire la struttura sportiva dove giocherete."

    appendix = custom_message + \
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

def print_summary(chat_id, reached_target, is_participants_command, update: Update, context: CallbackContext):
    players, day, time, target, custom_message, pitch, teams, bot_last_message_id = find_all_info_by_chat_id(chat_id)
    current_situation = beautify(players, day, time, target, custom_message, pitch)

    if bot_last_message_id is None or is_participants_command:
        markdown_error = False
        try:
            msg = context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown',
                                           text=current_situation)
        except:
            markdown_error = True
            error_message = "Sembra che tu abbia inserito nella descrizione un carattere speciale di telegram (`, *, _).\n" \
                            "Per favore cambiala con /setdescription <descrizione> assicurandoti di non inserire uno di questi caratteri.\n" \
                            "Se la tua intenzione era, invece, di formattare il testo, ricordati di usare anche il carattere di chiusura, come in questo *esempio*."
            msg = context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown',
                                           text=escape_markdown(error_message))
        if not markdown_error:
            try:
                context.bot.pin_chat_message(chat_id=update.effective_chat.id, message_id=msg.message_id)
            except:
                print("No admin rights to pin the message")
        update_bot_last_message_id_on_db(chat_id, msg.message_id)
    else:
        context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=bot_last_message_id, parse_mode='markdown', text=current_situation)
        try:
            context.bot.pin_chat_message(chat_id=update.effective_chat.id, message_id=bot_last_message_id)
        except:
            print("No admin rights to pin the message")

    if reached_target:
        set_payment_reminder(update, context, day, time)
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown',
                                 text="🚀 *SI GIOCA* 🚀 facciamo le squadre? /teams 😎")

