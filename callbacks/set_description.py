from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from behaviours.edit_summary import edit_summary
from behaviours.print_new_summary import print_new_summary
from db.queries import (
    find_row_by_chat_id,
    update_description_on_db,
    find_all_info_by_chat_id,
    update_bot_last_message_id_on_db,
)
from utils.utils import get_sender_mention, format_summary


async def set_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    row = find_row_by_chat_id(chat_id)

    if row is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            parse_mode="markdown",
            text="Prima di iniziare con le danze, avvia una partita, per farlo usa /start",
        )
        return

    # the raw text after the command: context.args would collapse newlines and repeated spaces
    description = update.message.text.split(None, 1)[1:]
    description = description[0].strip() if description else ""

    if description == "":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            parse_mode="markdown",
            text="Non hai inserito la descrizione: scrivi /setdescription <descrizione>",
        )
        return

    update_description_on_db(chat_id, description + "\n")
    sender = get_sender_mention(update)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        parse_mode="markdown",
        text=escape_markdown(f"Ok, {sender}! Ho aggiornato la descrizione!"),
    )

    players, day, time, target, default_message, pitch, _, bot_last_message_id = (
        find_all_info_by_chat_id(chat_id)
    )
    current_situation = format_summary(
        players, day, time, target, default_message, pitch
    )

    if bot_last_message_id is None:
        msg = await print_new_summary(current_situation, update, context)
        update_bot_last_message_id_on_db(chat_id, msg.message_id)
    else:
        await edit_summary(current_situation, bot_last_message_id, update, context)
