from telegram import Update
from telegram.ext import CallbackContext
from behaviours.print_new_summary import print_new_summary
from db.queries import find_row_by_chat_id, find_all_info_by_chat_id, update_bot_last_message_id_on_db
from utils.utils import format_summary

def participants(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_row_by_chat_id(chat_id)

    if row is None:
        answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
    else:
        players, day, time, target, default_message, pitch, _, _ = find_all_info_by_chat_id(chat_id)
        current_situation = format_summary(players, day, time, target, default_message, pitch)
        msg = print_new_summary(current_situation, update, context)
        update_bot_last_message_id_on_db(chat_id, msg.message_id)
