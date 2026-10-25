from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from behaviours.edit_summary import edit_summary
from behaviours.print_new_summary import print_new_summary
from db.queries import update_pitch_on_db, update_bot_last_message_id_on_db
from db.repository import get_match
from utils.utils import flatten_args, get_sender_mention, format_summary


async def set_pitch(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            answer = "Non hai inserito il campo: scrivi /setpitch <campo>"
            await context.bot.send_message(
                chat_id=update.effective_chat.id, parse_mode="markdown", text=answer
            )
        else:
            pitch = flatten_args(context.args)
            update_pitch_on_db(chat_id, pitch)
            sender = get_sender_mention(update)
            answer = "Ok, " + sender + "! Ho aggiornato il campo!"
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
