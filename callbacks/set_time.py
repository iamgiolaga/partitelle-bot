from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from behaviours.edit_summary import edit_summary
from behaviours.print_new_summary import print_new_summary
from behaviours.remove_job_if_exists import remove_job_if_exists
from behaviours.trigger_payment_reminder import trigger_payment_reminder
from db.queries import update_time_on_db, update_bot_last_message_id_on_db
from db.repository import get_match
from utils.utils import (
    flatten_args,
    get_sender_mention,
    format_summary,
    normalize_match_time,
)


async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if get_match(chat_id) is None:
        answer = (
            "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id, parse_mode="markdown", text=answer
        )
    else:
        if len(context.args) == 0:
            answer = "Non hai inserito l'orario: scrivi /settime <orario>"
            await context.bot.send_message(
                chat_id=update.effective_chat.id, parse_mode="markdown", text=answer
            )
        elif normalize_match_time(flatten_args(context.args)) is None:
            answer = (
                "L'orario non è valido: scrivi /settime <orario> nel formato HH:MM, "
                "ad esempio /settime 21:30"
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id, parse_mode="markdown", text=answer
            )
        else:
            time = normalize_match_time(flatten_args(context.args))
            update_time_on_db(chat_id, time)
            remove_job_if_exists(str(chat_id), context)
            match = get_match(chat_id)
            trigger_payment_reminder(update, context, match.day, match.time)
            sender = get_sender_mention(update)
            answer = (
                "Ok, " + sender + "! Ho impostato l'orario della partita alle " + time
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
                update_bot_last_message_id_on_db(chat_id, msg.message_id)
            else:
                await edit_summary(
                    current_situation, match.summary_message_id, update, context
                )
