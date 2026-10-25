from telegram import Update
from telegram.ext import ContextTypes
from db.repository import get_match, delete_match


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if get_match(chat_id) is None:
        answer = (
            "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
        )
    else:
        answer = "Ho cancellato la partita."
        delete_match(chat_id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, parse_mode="markdown", text=answer
    )
