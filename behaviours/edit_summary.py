import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def edit_summary(
    current_situation,
    bot_last_message_id,
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=bot_last_message_id,
        parse_mode="markdown",
        text=current_situation,
    )
    try:
        await context.bot.pin_chat_message(
            chat_id=update.effective_chat.id, message_id=bot_last_message_id
        )
    except Exception:
        logger.warning("No admin rights to pin the message")
