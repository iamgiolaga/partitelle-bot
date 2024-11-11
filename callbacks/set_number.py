from telegram import Update
from telegram.ext import CallbackContext
from telegram.utils.helpers import escape_markdown
from behaviours.edit_summary import edit_summary
from behaviours.print_new_summary import print_new_summary
from behaviours.remove_job_if_exists import remove_job_if_exists
from behaviours.trigger_payment_reminder import trigger_payment_reminder
from db.queries import find_all_info_by_chat_id, update_teams_on_db, update_target_on_db, update_bot_last_message_id_on_db
from utils.utils import get_sender_name, exclude_maybe, format_summary

def set_number(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_all_info_by_chat_id(chat_id)

    if row is None:
        answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
    else:
        teams = row[-2]
        try:
            if len(context.args) > 1:
                answer = "Hai messo più di un numero, probabilmente intendevi /setnumber " + context.args[0]
            else:
                chosen_number_str = context.args[0]
                sender = "@" + get_sender_name(update)
                players = row[0]
                if players is None:
                    participants_num = 0
                else:
                    participants_num = len(exclude_maybe(players))

                if chosen_number_str.isnumeric():
                    chosen_number = int(chosen_number_str)
                    if chosen_number <= 0 or chosen_number > 40:
                        answer = "Non è un numero valido di partecipanti 🌚"
                    elif chosen_number < 2:
                        answer = "Il numero che hai inserito non va bene 👎"
                    elif chosen_number < participants_num:
                        answer = "Hai ridotto i partecipanti ma c'è ancora gente nella lista. Io non saprei chi togliere, puoi farlo tu? 🙏"
                    else:
                        if teams is not None:
                            update_teams_on_db(chat_id, None)
                            remove_job_if_exists(str(chat_id), context)
                            answer = "*SQUADRE ANNULLATE*"
                            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)

                        update_target_on_db(chat_id, chosen_number)
                        answer = "Ok, " + sender + "! Ho impostato il numero di partecipanti a " + str(chosen_number)
                        reached_target = players and participants_num == chosen_number
                        players, day, time, target, default_message, pitch, teams, bot_last_message_id = find_all_info_by_chat_id(chat_id)
                        current_situation = format_summary(players, day, time, target, default_message, pitch)
                        if bot_last_message_id is None:
                            msg = print_new_summary(current_situation, update, context)
                            update_bot_last_message_id_on_db(chat_id, msg.message_id)
                        else:
                            edit_summary(current_situation, bot_last_message_id, update, context)

                        if reached_target:
                            trigger_payment_reminder(update, context, day, time)
                            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown',
                                                     text="🚀 *SI GIOCA* 🚀 facciamo le squadre? /teams 😎")
                else:
                    answer = sender + ", quello ti sembra un numero? 😂"

        except:
            answer = "Non hai inserito il numero: scrivi /setnumber <numero>"
    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=escape_markdown(answer))
