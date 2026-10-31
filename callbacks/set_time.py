from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from behaviours.edit_summary import edit_summary
from behaviours.print_new_summary import print_new_summary
from behaviours.remove_job_if_exists import remove_job_if_exists
from behaviours.trigger_payment_reminder import trigger_payment_reminder
from db import repository
from db.repository import get_match, set_summary_message_id
from domain.schedule import format_time, parse_time, with_time
from utils.utils import flatten_args, get_sender_mention, format_summary


async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    match = get_match(chat_id)
    if match is None:
        answer = (
            "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id, parse_mode="markdown", text=answer
        )
        return

    if len(context.args) == 0:
        answer = "Non hai inserito l'orario: scrivi /settime <orario>"
        await context.bot.send_message(
            chat_id=update.effective_chat.id, parse_mode="markdown", text=answer
        )
        return

    sender = get_sender_mention(update)
    at = parse_time(flatten_args(context.args))
    if at is None:
        answer = (
            f"Non ho capito l'ora, {sender}: "
            "scrivila come HH:MM, per esempio /settime 21:30"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            parse_mode="markdown",
            text=escape_markdown(answer),
        )
        return

    starts = with_time(match.starts, at)
    repository.set_starts(chat_id, starts)
    remove_job_if_exists(str(chat_id), context)
    trigger_payment_reminder(update, context, starts)
    answer = (
        "Ok, "
        + sender
        + "! Ho impostato l'orario della partita alle "
        + format_time(starts)
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        parse_mode="markdown",
        text=escape_markdown(answer),
    )
    match = get_match(chat_id)
    current_situation = format_summary(match)
    if match.summary_message_id is None:
        msg = await print_new_summary(current_situation, update, context)
        set_summary_message_id(chat_id, msg.message_id)
    else:
        await edit_summary(current_situation, match.summary_message_id, update, context)
