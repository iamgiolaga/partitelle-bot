from telegram import Update
from telegram.ext import CallbackContext
from db.queries import find_row_by_chat_id, update_pitch_on_db
from utils.behaviours import flatten_args, get_sender_name, print_summary
from telegram.utils.helpers import escape_markdown

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
            context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=escape_markdown(answer))
            print_summary(chat_id, False, False, update, context)
