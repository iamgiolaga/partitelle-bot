from telegram import Update
from telegram.ext import CallbackContext
from db.queries import find_row_by_chat_id, find_all_info_by_chat_id, update_day_on_db
from utils.behaviours import flatten_args, get_sender_name, print_summary, remove_job_if_exists, set_payment_reminder
from telegram.utils.helpers import escape_markdown

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
            remove_job_if_exists(str(chat_id), context)
            players, day, time, target, custom_message, pitch, teams, bot_last_message_id = find_all_info_by_chat_id(chat_id)
            set_payment_reminder(update, context, day, time)
            sender = "@" + get_sender_name(update)
            answer = "Ok, " + sender + "! Ho impostato il giorno della partita il " + day
            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=escape_markdown(answer))
            print_summary(chat_id, False, False, update, context)