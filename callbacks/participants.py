from telegram import Update
from telegram.ext import ContextTypes
from behaviours.print_new_summary import print_new_summary
from db.repository import set_summary_message_id
from db.repository import get_match
from utils.utils import format_summary


async def participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    match = get_match(chat_id)

    if match is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            parse_mode="markdown",
            text="Prima di iniziare con le danze, avvia una partita, per farlo usa /start",
        )
        return

    current_situation = format_summary(match)
    msg = await print_new_summary(current_situation, update, context)
    set_summary_message_id(chat_id, msg.message_id)
