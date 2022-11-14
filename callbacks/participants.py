from telegram import Update
from telegram.ext import CallbackContext
from db.queries import find_row_by_chat_id
from utils.behaviours import print_summary

def participants(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_row_by_chat_id(chat_id)

    if row is None:
        answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
    else:
        print_summary(chat_id, False, True, update, context)
