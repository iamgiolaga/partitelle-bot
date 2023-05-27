from telegram import Update
from telegram.ext import CallbackContext
from telegram.utils.helpers import escape_markdown
from db.queries import update_bot_last_message_id_on_db

def print_new_summary(chat_id, current_situation, update: Update, context: CallbackContext):
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