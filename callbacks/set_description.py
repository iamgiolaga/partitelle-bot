from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from behaviours.edit_summary import edit_summary
from behaviours.print_new_summary import print_new_summary
from db.queries import update_description_on_db, update_bot_last_message_id_on_db
from db.repository import get_match
from utils.utils import get_sender_mention, format_summary


async def set_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if get_match(chat_id) is None:
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

    match = get_match(chat_id)
    current_situation = format_summary(match)

    if match.summary_message_id is None:
        msg = await print_new_summary(current_situation, update, context)
        update_bot_last_message_id_on_db(chat_id, msg.message_id)
    else:
        await edit_summary(current_situation, match.summary_message_id, update, context)
