from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from behaviours.edit_summary import edit_summary
from behaviours.print_new_summary import print_new_summary
from behaviours.remove_job_if_exists import remove_job_if_exists
from behaviours.trigger_payment_reminder import trigger_payment_reminder
from db import repository
from db.repository import get_match, set_summary_message_id
from domain.schedule import format_day, parse_day, with_day
from utils.utils import flatten_args, get_sender_mention, format_summary


async def set_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    match = get_match(chat_id)
    if match is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            parse_mode="markdown",
            text="Prima di iniziare con le danze, avvia una partita, per farlo usa /start",
        )
        return

    if len(context.args) == 0:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            parse_mode="markdown",
            text="Non hai inserito il giorno: scrivi /setday <giorno>",
        )
        return

    sender = get_sender_mention(update)
    day = parse_day(flatten_args(context.args))
    if day is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            parse_mode="markdown",
            text=escape_markdown(
                f"Non ho capito il giorno, {sender}: "
                "scrivilo come GG/MM/AAAA, per esempio /setday 25/10/2026"
            ),
        )
        return

    starts = with_day(match.starts, day)
    repository.set_starts(chat_id, starts)
    remove_job_if_exists(str(chat_id), context)
    trigger_payment_reminder(update, context, starts)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        parse_mode="markdown",
        text=escape_markdown(
            f"Ok, {sender}! Ho impostato il giorno della partita il {format_day(starts)}"
        ),
    )

    match = get_match(chat_id)
    current_situation = format_summary(match)

    if match.summary_message_id is None:
        msg = await print_new_summary(current_situation, update, context)
        set_summary_message_id(chat_id, msg.message_id)
    else:
        await edit_summary(current_situation, match.summary_message_id, update, context)
