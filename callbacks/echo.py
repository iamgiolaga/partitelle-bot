from telegram import Update
from telegram.ext import CallbackContext
from db.queries import find_row_by_chat_id, find_all_info_by_chat_id, update_players_on_db, update_teams_on_db, is_already_present
from utils.behaviours import flatten_args, get_sender_name, print_summary, filter_maybe_placeholders, swap_players, remove_job_if_exists
from utils.macros import maybe_placeholder
from telegram.utils.helpers import escape_markdown

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
                    answer = 'Ma ' + sender + ', sei già nella lista'
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
                        answer = 'Siete già in ' + str(target)
                        show_summary = False

            elif new_message.startswith('aggiungi'):
                to_be_added = flatten_args(new_message.split(" ")[1:])
                if is_already_present(chat_id, to_be_added):
                    answer = to_be_added + ' è già nella lista'
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
                        answer = 'Siete già in ' + str(target)
                        show_summary = False

            elif new_message == 'proponimi':
                sender = "@" + get_sender_name(update)
                if is_already_present(chat_id, sender + maybe_placeholder):
                    answer = 'Ma ' + sender + ', sei già in forse'
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
                    else:
                        answer = 'Siete già in ' + str(target)
                        show_summary = False

            elif new_message.startswith('proponi'):
                to_be_added = flatten_args(new_message.split(" ")[1:])
                if is_already_present(chat_id, to_be_added + maybe_placeholder):
                    answer = to_be_added + ' è già nella lista'
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
                    else:
                        answer = 'Siete già in ' + str(target)
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
                        answer = to_be_removed + ' non è nella lista. Chi dovrei togliere?'
                        show_summary = False

            elif new_message.startswith('scambia'):
                to_be_parsed = flatten_args(new_message.split(" ")[1:])
                x, y = to_be_parsed.split(" con ")
                show_summary = False
                if teams is None:
                    answer = "Per usare questa funzionalità devi prima formare delle squadre con /teams"
                else:
                    if not is_already_present(chat_id, x):
                        answer = x + " non c'è"
                    elif not is_already_present(chat_id, y):
                        answer = y + " non c'è"
                    else:
                        error, teams = swap_players(teams, x, y)
                        if error:
                            answer = x + " e " + y + " sono nella stessa squadra!"
                        else:
                            update_teams_on_db(chat_id, teams)
                            answer = "Perfetto, ho scambiato " + x + " con " + y

            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=escape_markdown(answer))

            if revoked_teams:
                update_teams_on_db(chat_id, None)
                remove_job_if_exists(str(chat_id), context)
                answer = "*SQUADRE ANNULLATE*"
                context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)

            if show_summary:
                print_summary(chat_id, reached_target, False, update, context)
