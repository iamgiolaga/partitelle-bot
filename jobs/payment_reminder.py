import logging

from telegram.ext import ContextTypes

from db.repository import set_summary_message_id

logger = logging.getLogger(__name__)


async def payment_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.name

    msg = await context.bot.send_message(
        chat_id,
        text="Ciao bestie 😎, com'è andata la partita? C'è qualcuno che non ha ancora pagato la sua quota?",
    )

    try:
        await context.bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id)
    except Exception:
        logger.warning("No admin rights to pin the message")

    set_summary_message_id(chat_id, msg.message_id)
