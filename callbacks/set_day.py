from telegram import Update
from telegram.ext import CallbackContext
from telegram.utils.helpers import escape_markdown
from behaviours.edit_summary import edit_summary
from behaviours.print_new_summary import print_new_summary
from behaviours.remove_job_if_exists import remove_job_if_exists
from behaviours.trigger_payment_reminder import trigger_payment_reminder
from db.queries import (
    find_row_by_chat_id,
    find_all_info_by_chat_id,
    update_day_on_db,
    update_bot_last_message_id_on_db,
)
from utils.utils import flatten_args, get_sender_name, format_summary


def set_day(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_row_by_chat_id(chat_id)

    if row is None:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            parse_mode="markdown",
            text="Prima di iniziare con le danze, avvia una partita, per farlo usa /start",
        )
        return

    if len(context.args) == 0:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            parse_mode="markdown",
            text="Non hai inserito il giorno: scrivi /setday <giorno>",
        )
        return

    day = flatten_args(context.args)
    update_day_on_db(chat_id, day)
    remove_job_if_exists(str(chat_id), context)
    players, day, time, target, _, pitch, _, bot_last_message_id = (
        find_all_info_by_chat_id(chat_id)
    )
    trigger_payment_reminder(update, context, day, time)
    sender = "@" + get_sender_name(update)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        parse_mode="markdown",
        text=escape_markdown(
            f"Ok, {sender}! Ho impostato il giorno della partita il {day}"
        ),
    )

    players, day, time, target, default_message, pitch, _, bot_last_message_id = (
        find_all_info_by_chat_id(chat_id)
    )
    current_situation = format_summary(
        players, day, time, target, default_message, pitch
    )

    if bot_last_message_id is None:
        msg = print_new_summary(current_situation, update, context)
        update_bot_last_message_id_on_db(chat_id, msg.message_id)
    else:
        edit_summary(current_situation, bot_last_message_id, update, context)
