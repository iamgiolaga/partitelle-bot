from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from behaviours.edit_summary import edit_summary
from behaviours.print_new_summary import print_new_summary
from behaviours.remove_job_if_exists import remove_job_if_exists
from behaviours.trigger_payment_reminder import trigger_payment_reminder
from db.queries import update_day_on_db, update_bot_last_message_id_on_db
from db.repository import get_match
from utils.utils import flatten_args, get_sender_mention, format_summary


async def set_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if get_match(chat_id) is None:
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

    day = flatten_args(context.args)
    update_day_on_db(chat_id, day)
    remove_job_if_exists(str(chat_id), context)
    match = get_match(chat_id)
    day = match.day
    trigger_payment_reminder(update, context, day, match.time)
    sender = get_sender_mention(update)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        parse_mode="markdown",
        text=escape_markdown(
            f"Ok, {sender}! Ho impostato il giorno della partita il {day}"
        ),
    )

    match = get_match(chat_id)
    current_situation = format_summary(match)

    if match.summary_message_id is None:
        msg = await print_new_summary(current_situation, update, context)
        update_bot_last_message_id_on_db(chat_id, msg.message_id)
    else:
        await edit_summary(current_situation, match.summary_message_id, update, context)
