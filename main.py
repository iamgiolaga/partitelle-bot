from telegram.ext import Updater
from telegram import Update
from telegram.ext import CallbackContext
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
import datetime
from datetime import datetime, timedelta
from config import config
import logging
import psycopg2
import os
import json
import random

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

TOKEN = os.getenv("TOKEN") # this is an env variable to hide token

connection = None
default_day = None
default_time = "21:00"
default_target = 10
custom_message = "5 goal di scarto e le squadre si _potrebbero_ cambiare \n" \
               "6 goal di scarto e le squadre si *devono* cambiare \n"\
               "(ditelo a chiunque invitate) \n"\
               "*PORTARE UNA MAGLIA BIANCA E UNA COLORATA*\n"
maybe_placeholder = "%is%maybe%present"

def connect():
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # read connection parameters
        params = config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        conn.autocommit = True

        # create a cursor
        cur = conn.cursor()

        # execute a statement
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')

        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)

        return cur
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    # finally:
    #     if conn is not None:
    #         conn.close()
    #         print('Database connection closed.')

def compute_next_wednesday():
    return get_next_weekday((datetime.today().strftime('%d/%m/%Y')), 2)

def get_next_weekday(startdate, weekday):
    """
    @startdate: given date
    @weekday: week day as a integer, between 0 (Monday) to 6 (Sunday)
    """
    d = datetime.strptime(startdate, '%d/%m/%Y')
    t = timedelta((7 + weekday - d.weekday()) % 7)
    return (d + t).strftime('%d/%m/%Y')

def get_sender_name(source):
    return source.message.from_user.username.lower()

def delete_row_on_db(chat_id):
    connection.execute('DELETE FROM all_players WHERE chat_id=%s', [str(chat_id)])

def is_already_present(chat_id, name):
    connection.execute('SELECT players FROM all_players WHERE chat_id=%s', [str(chat_id)])
    current_players = connection.fetchone()
    if current_players is None or current_players[0] is None:
        return False
    return name in current_players[0]

def create_chat_id_row(chat_id):
    default_day = "Mercoled?? " + compute_next_wednesday()
    connection.execute("INSERT INTO all_players (chat_id, players, day, time, target, custom_message, pitch, teams, bot_last_message_id) "
                       "VALUES ( %s, null, %s, %s, %s, %s, null, null, null)", [str(chat_id), default_day, default_time, str(default_target), custom_message])

def find_all_info_by_chat_id(chat_id):
    connection.execute('SELECT players, day, time, target, custom_message, pitch, teams, bot_last_message_id FROM all_players WHERE chat_id=%s', [str(chat_id)])
    return connection.fetchone()

def find_row_by_chat_id(chat_id):
    connection.execute('SELECT chat_id, players FROM all_players WHERE chat_id=%s', [str(chat_id)])
    return connection.fetchone()

def update_bot_last_message_id_on_db(chat_id, msg_id):
    connection.execute('UPDATE all_players SET bot_last_message_id = %s WHERE chat_id= %s', [str(msg_id), str(chat_id)])

def update_target_on_db(chat_id, target):
    connection.execute('UPDATE all_players SET target = %s WHERE chat_id= %s', [str(target), str(chat_id)])

def update_day_on_db(chat_id, day):
    connection.execute("UPDATE all_players SET day = %s WHERE chat_id= %s", [day, str(chat_id)])

def update_time_on_db(chat_id, time):
    connection.execute("UPDATE all_players SET time = %s WHERE chat_id= %s", [time, str(chat_id)])

def update_description_on_db(chat_id, description):
    connection.execute("UPDATE all_players SET custom_message = %s WHERE chat_id= %s", [description, str(chat_id)])

def update_pitch_on_db(chat_id, pitch):
    connection.execute("UPDATE all_players SET pitch = %s WHERE chat_id= %s", [pitch, str(chat_id)])

def update_teams_on_db(chat_id, teams):
    connection.execute("UPDATE all_players SET teams = %s WHERE chat_id= %s", [teams, str(chat_id)])

def update_players_on_db(chat_id, new_entry, action):
    connection.execute('SELECT players FROM all_players WHERE chat_id=%s', [str(chat_id)])
    current_players = connection.fetchone()
    if current_players[0] is None:
        connection.execute("UPDATE all_players SET players = %s WHERE chat_id=%s", ['{'+new_entry+'}', str(chat_id)])
    else:
        result = "{"
        if action == "add":
            current_players[0].append(new_entry)
            for index, player in enumerate(current_players[0]):
                if index < len(current_players):
                    result = result + player + ","
                else:
                    last_char_index = len(result) - 1
                    if result[last_char_index] == "}":
                        result = result[0:last_char_index] + result[last_char_index].replace("}", ",")
                    result = result + player + "}"
        elif action == "remove":
            current_players[0].remove(new_entry)
            for index, player in enumerate(current_players[0]):
                if index < len(current_players[0])-1 and len(current_players[0]) > 1:
                    result = result + player + ","
                else:
                    result = result + player + "}"

            if len(current_players[0]) == 0:
                result = None

        connection.execute('UPDATE all_players SET players = %s WHERE chat_id=%s', [result, str(chat_id)])

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

def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_all_info_by_chat_id(chat_id)

    if row is None:
        create_chat_id_row(chat_id)

    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown',
                             text="Ciao bestie ????, chi c'?? per il prossimo calcetto? \n"
                                  "\n"
                                  "- se sei in forse scrivi _proponimi_, \n" \
                                  "- se vuoi proporre qualcuno scrivi _proponi <nome>_, \n" \
                                  "- per essere aggiunto o confermato rispondi _aggiungimi_,\n" \
                                  "- per aggiungere o confermare qualcuno usa _aggiungi <nome>_,\n" \
                                  "- per essere rimosso _toglimi_, \n" \
                                  "- per rimuovere qualcuno _togli <nome>_, \n" \
                                  "- per modificare le squadre scrivi _scambia <nome 1> con <nome 2>_. \n\n" \
                                  "Posso anche pinnare i messaggi se vuoi " \
                                  "ma per farlo ricordati di aggiungermi come amministratore."
                             )

def beautify(all_players, day, time, target, custom_message, pitch):
    player_list = ""

    prefix = "*GIORNO*: " + day + " | " + time + "\n"\

    if pitch is None:
        pitch = "Usa il comando /setpitch <campo> per inserire la struttura sportiva dove giocherete."

    appendix = custom_message + \
                "\n"\
                "*CAMPO*: \n"\
                + pitch

    for i in range(0, target):
        if all_players and i < len(all_players):
            player = all_players[i]
            if player.endswith(maybe_placeholder):
                player = player.replace(maybe_placeholder, "")
                player_list = player_list + str(i+1) + ". " + player + " ??? \n"
            else:
                player_list = player_list + str(i+1) + ". " + player + " ??? \n"
        else:
            player_list = player_list + str(i+1) + ". ??? \n"

    return prefix + "\n" + player_list + "\n" + appendix

def print_summary(chat_id, reached_target, is_participants_command, update: Update, context: CallbackContext):
    players, day, time, target, custom_message, pitch, teams, bot_last_message_id = find_all_info_by_chat_id(chat_id)
    current_situation = beautify(players, day, time, target, custom_message, pitch)

    if bot_last_message_id is None or is_participants_command:
        msg = context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown',
                                 text=current_situation)
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
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown',
                                 text="???? *SI GIOCA* ???? facciamo le squadre? /teams ????")

def print_teams(teams, update: Update, context: CallbackContext):
    json_teams = json.loads(teams)
    black_team = json_teams["black"]
    white_team = json_teams["white"]

    teams_message = "*SQUADRA NERA* \n"
    for player in black_team:
        teams_message = teams_message + " - " + player + "\n"

    teams_message = teams_message + "\n"
    teams_message = teams_message + "*SQUADRA BIANCA* \n"
    for player in white_team:
        teams_message = teams_message + " - " + player + "\n"

    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=teams_message)

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


def set_number(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_all_info_by_chat_id(chat_id)

    if row is None:
        answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
    else:
        teams = row[-2]
        try:
            if len(context.args) > 1:
                answer = "Hai messo pi?? di un numero, probabilmente intendevi /setnumber " + context.args[0]
            else:
                choosen_number_str = context.args[0]
                sender = "@" + get_sender_name(update)
                players = row[0]
                if players is None:
                    participants_num = 0
                else:
                    participants_num = len(filter_maybe_placeholders(players))

                if choosen_number_str.isnumeric():
                    choosen_number = int(choosen_number_str)
                    if choosen_number <= 0 or choosen_number > 40:
                        answer = "Non ?? un numero valido di partecipanti ????"
                    elif choosen_number < participants_num:
                        answer = "Hai ridotto i partecipanti ma c'?? ancora gente nella lista. Io non saprei chi togliere, puoi farlo tu? ????"
                    elif choosen_number < 2:
                        answer = "Il numero che hai inserito non va bene ????"
                    else:
                        if teams is not None:
                            update_teams_on_db(chat_id, None)
                            answer = "*SQUADRE ANNULLATE*"
                            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown',
                                                     text=answer)

                        update_target_on_db(chat_id, choosen_number)
                        answer = "Ok, " + sender + "! Ho impostato il numero di partecipanti a " + str(choosen_number)
                        reached_target = players and participants_num == choosen_number
                        print_summary(chat_id, reached_target, False, update, context)
                else:
                    answer = sender + ", quello ti sembra un numero? ????"

        except:
            answer = "Non hai inserito il numero: scrivi /setnumber <numero>"
    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)

def set_day(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_row_by_chat_id(chat_id)

    if row is None:
        answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
    else:
        if len(context.args) == 0:
            answer = "Non hai inserito il giorno: scrivi /setday <giorno>"
            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
        else:
            day = flatten_args(context.args)
            update_day_on_db(chat_id, day)
            sender = "@" + get_sender_name(update)
            answer = "Ok, " + sender + "! Ho impostato il giorno della partita il " + day
            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
            print_summary(chat_id, False, False, update, context)

def set_time(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_row_by_chat_id(chat_id)

    if row is None:
        answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
    else:
        if len(context.args) == 0:
            answer = "Non hai inserito l'orario: scrivi /settime <orario>"
            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
        else:
            time = flatten_args(context.args)
            update_time_on_db(chat_id, time)
            sender = "@" + get_sender_name(update)
            answer = "Ok, " + sender + "! Ho impostato l'orario della partita alle " + time
            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
            print_summary(chat_id, False, False, update, context)

def set_description(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_row_by_chat_id(chat_id)

    if row is None:
        answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
    else:
        if len(context.args) == 0:
            answer = "Non hai inserito la descrizione: scrivi /setdescription <descrizione>"
            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
        else:
            description = flatten_args(context.args) + "\n"
            update_description_on_db(chat_id, description)
            sender = "@" + get_sender_name(update)
            answer = "Ok, " + sender + "! Ho aggiornato la descrizione!"
            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
            print_summary(chat_id, False, False, update, context)

def set_pitch(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_row_by_chat_id(chat_id)

    if row is None:
        answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
    else:
        if len(context.args) == 0:
            answer = "Non hai inserito il campo: scrivi /setpitch <campo>"
            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
        else:
            pitch = flatten_args(context.args)
            update_pitch_on_db(chat_id, pitch)
            sender = "@" + get_sender_name(update)
            answer = "Ok, " + sender + "! Ho aggiornato il campo!"
            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
            print_summary(chat_id, False, False, update, context)

def participants(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_row_by_chat_id(chat_id)

    if row is None:
        answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
    else:
        print_summary(chat_id, False, True, update, context)

def teams(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_all_info_by_chat_id(chat_id)

    if row is None:
        answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)

    else:
        players = row[0]
        target = row[3]
        teams = row[-2]
        if players is None:
            participants_num = 0
        else:
            participants_num = len(filter_maybe_placeholders(players))
        reached_target = players and participants_num == target

        if teams is not None:
            print_teams(json.dumps(teams), update, context)
        else:
            if target % 2 == 0:
                if not reached_target:
                    answer = "Prima di poter fare le squadre, devi raggiungere " + str(target) + " partecipanti"
                    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
                else:
                    generated_teams = generate_teams(players)
                    update_teams_on_db(chat_id, generated_teams)
                    print_teams(generated_teams, update, context)
            else:
                answer = "Per usare questa funzionalit?? dovete essere in un numero pari di partecipanti"
                context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)

def stop(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_row_by_chat_id(chat_id)

    if row is None:
        answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
    else:
        answer = 'Ho cancellato la partita.'
        delete_row_on_db(chat_id)
    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)

def help_func(update: Update, context: CallbackContext):
    answer = "Ecco a te la lista completa dei comandi di questo bot: \n" \
             "- se sei in forse scrivi _proponimi_, \n" \
             "- se vuoi proporre qualcuno scrivi _proponi <nome>_, \n" \
             "- per essere aggiunto o confermato rispondi _aggiungimi_,\n" \
             "- per aggiungere o confermare qualcuno usa _aggiungi <nome>_,\n" \
             "- per essere rimosso _toglimi_, \n" \
             "- per rimuovere qualcuno _togli <nome>_, \n" \
             "- per modificare le squadre scrivi _scambia <nome 1> con <nome 2>_. \n\n" \
             "Posso anche pinnare i messaggi se vuoi " \
             "ma per farlo ricordati di aggiungermi come amministratore.\n" \
             "\n" \
             "/start - Crea una nuova partita \n" \
             "/setnumber - Imposta il numero di partecipanti \n" \
             "/setday - Imposta il giorno della partita \n" \
             "/settime - Imposta l???orario della partita \n" \
             "/setdescription - Imposta la descrizione sotto i partecipanti \n" \
             "/setpitch - Imposta il campo \n" \
             "/participants - Mostra i partecipanti della partita attuale \n" \
             "/teams - Mostra le squadre della partita attuale \n" \
             "/stop - Rimuovi la partita \n" \
             "/help - Mostra la lista di comandi disponibili"

    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)

def echo(update: Update, context: CallbackContext):
    new_message = update.message.text.lower()
    chat_id = update.message.chat_id
    answer = None
    show_summary = True
    reached_target = False
    revoked_teams = False

    if new_message in ['aggiungimi', 'toglimi', 'proponimi'] \
            or new_message.startswith('aggiungi') \
            or new_message.startswith('togli') \
            or new_message.startswith('proponi') \
            or new_message.startswith('scambia'):
        row = find_row_by_chat_id(chat_id)
        if row is None:
            answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
        else:
            players, day, time, target, custom_message, pitch, teams, bot_last_message_id = find_all_info_by_chat_id(chat_id)
            if new_message == 'aggiungimi':
                sender = "@" + get_sender_name(update)
                if is_already_present(chat_id, sender):
                    answer = 'Ma ' + sender + ', sei gi?? nella lista'
                    show_summary = False
                elif is_already_present(chat_id, sender + maybe_placeholder):
                    answer = 'Ok, ' + sender + ', ti confermo'
                    update_players_on_db(chat_id, sender + maybe_placeholder, "remove")
                    update_players_on_db(chat_id, sender, "add")
                    show_summary = True
                    reached_target = players and len(filter_maybe_placeholders(players)) + 1 == target
                else:
                    if not players or len(players) <= target - 1:
                        answer = 'Ok, ' + sender + ', ti aggiungo'
                        update_players_on_db(chat_id, sender, "add")
                        show_summary = True
                        reached_target = players and len(filter_maybe_placeholders(players)) + 1 == target
                    else:
                        answer = 'Siete gi?? in ' + str(target)
                        show_summary = False

            elif new_message.startswith('aggiungi'):
                to_be_added = flatten_args(new_message.split(" ")[1:])
                if is_already_present(chat_id, to_be_added):
                    answer = to_be_added + ' ?? gi?? nella lista'
                    show_summary = False
                elif is_already_present(chat_id, to_be_added + maybe_placeholder):
                    answer = 'Ok, ' + to_be_added + ', ti confermo'
                    update_players_on_db(chat_id, to_be_added + maybe_placeholder, "remove")
                    update_players_on_db(chat_id, to_be_added, "add")
                    show_summary = True
                    reached_target = players and len(filter_maybe_placeholders(players)) + 1 == target
                else:
                    if not players or len(players) <= target - 1:
                        answer = 'Ok, aggiungo ' + to_be_added
                        update_players_on_db(chat_id, to_be_added, "add")
                        show_summary = True
                        reached_target = players and len(filter_maybe_placeholders(players)) + 1 == target
                    else:
                        answer = 'Siete gi?? in ' + str(target)
                        show_summary = False

            elif new_message == 'proponimi':
                sender = "@" + get_sender_name(update)
                if is_already_present(chat_id, sender + maybe_placeholder):
                    answer = 'Ma ' + sender + ', sei gi?? in forse'
                    show_summary = False
                elif is_already_present(chat_id, sender):
                    answer = 'Ok, ' + sender + ', ti metto in forse'
                    update_players_on_db(chat_id, sender, "remove")
                    update_players_on_db(chat_id, sender + maybe_placeholder, "add")
                    show_summary = True
                else:
                    if not players or len(players) <= target - 1:
                        answer = 'Ok, ' + sender + ', ti propongo'
                        update_players_on_db(chat_id, sender + maybe_placeholder, "add")
                        show_summary = True
                        reached_target = players and len(filter_maybe_placeholders(players)) + 1 == target
                    else:
                        answer = 'Siete gi?? in ' + str(target)
                        show_summary = False

            elif new_message.startswith('proponi'):
                to_be_added = flatten_args(new_message.split(" ")[1:])
                if is_already_present(chat_id, to_be_added + maybe_placeholder):
                    answer = to_be_added + ' ?? gi?? nella lista'
                    show_summary = False
                elif is_already_present(chat_id, to_be_added):
                    answer = 'Va bene, metto in forse ' + to_be_added
                    update_players_on_db(chat_id, to_be_added, "remove")
                    update_players_on_db(chat_id, to_be_added + maybe_placeholder, "add")
                    show_summary = True
                else:
                    if not players or len(players) <= target - 1:
                        answer = 'Ok, propongo ' + to_be_added
                        update_players_on_db(chat_id, to_be_added + maybe_placeholder, "add")
                        show_summary = True
                        reached_target = players and len(filter_maybe_placeholders(players)) + 1 == target
                    else:
                        answer = 'Siete gi?? in ' + str(target)
                        show_summary = False

            elif new_message == 'toglimi':
                sender = "@" + get_sender_name(update)
                if is_already_present(chat_id, sender):
                    answer = 'Mamma mia... che paccaro'
                    update_players_on_db(chat_id, sender, "remove")
                    show_summary = True
                    revoked_teams = teams is not None
                else:
                    if is_already_present(chat_id, sender + maybe_placeholder):
                        answer = "Peccato, un po' ci avevo sperato"
                        update_players_on_db(chat_id, sender + maybe_placeholder, "remove")
                        show_summary = True
                        revoked_teams = teams is not None
                    else:
                        answer = 'Non eri in lista neanche prima'
                        show_summary = False

            elif new_message.startswith('togli'):
                to_be_removed = flatten_args(new_message.split(" ")[1:])
                if is_already_present(chat_id, to_be_removed):
                    answer = 'Che vergogna, ' + to_be_removed
                    update_players_on_db(chat_id, to_be_removed, "remove")
                    show_summary = True
                    revoked_teams = teams is not None
                else:
                    if is_already_present(chat_id, to_be_removed + maybe_placeholder):
                        answer = "Davvero? Ma " + to_be_removed + ", ne sei proprio sicuro?"
                        update_players_on_db(chat_id, to_be_removed + maybe_placeholder, "remove")
                        show_summary = True
                        revoked_teams = teams is not None
                    else:
                        answer = to_be_removed + ' non ?? nella lista. Chi dovrei togliere?'
                        show_summary = False

            elif new_message.startswith('scambia'):
                to_be_parsed = flatten_args(new_message.split(" ")[1:])
                x, y = to_be_parsed.split(" con ")
                show_summary = False
                if teams is None:
                    answer = "Per usare questa funzionalit?? devi prima formare delle squadre con /teams"
                else:
                    if not is_already_present(chat_id, x):
                        answer = x + " non c'??"
                    elif not is_already_present(chat_id, y):
                        answer = y + " non c'??"
                    else:
                        error, teams = swap_players(teams, x, y)
                        if error:
                            answer = x + " e " + y + " sono nella stessa squadra!"
                        else:
                            update_teams_on_db(chat_id, teams)
                            answer = "Perfetto, ho scambiato " + x + " con " + y

            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)

            if revoked_teams:
                update_teams_on_db(chat_id, None)
                answer = "*SQUADRE ANNULLATE*"
                context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)

            if show_summary:
                print_summary(chat_id, reached_target, False, update, context)

if __name__ == '__main__':
    connection = connect()

    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    set_number_handler = CommandHandler('setnumber', set_number)
    dispatcher.add_handler(set_number_handler)

    set_day_handler = CommandHandler('setday', set_day)
    dispatcher.add_handler(set_day_handler)

    set_time_handler = CommandHandler('settime', set_time)
    dispatcher.add_handler(set_time_handler)

    set_description_handler = CommandHandler('setdescription', set_description)
    dispatcher.add_handler(set_description_handler)

    set_pitch_handler = CommandHandler('setpitch', set_pitch)
    dispatcher.add_handler(set_pitch_handler)

    participants_handler = CommandHandler('participants', participants)
    dispatcher.add_handler(participants_handler)

    teams_handler = CommandHandler('teams', teams)
    dispatcher.add_handler(teams_handler)

    stop_handler = CommandHandler('stop', stop)
    dispatcher.add_handler(stop_handler)

    help_handler = CommandHandler('help', help_func)
    dispatcher.add_handler(help_handler)

    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    #updater.start_polling()
    updater.start_webhook(listen="0.0.0.0", webhook_url="https://partitelle-bot.herokuapp.com/"+TOKEN, url_path=TOKEN, port=int(os.environ.get('PORT', 5000)))
    updater.idle()
