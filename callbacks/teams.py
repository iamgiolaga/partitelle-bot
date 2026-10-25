from telegram import Update
from telegram.ext import ContextTypes
from db.repository import get_match, save_teams
from utils.utils import format_teams, generate_teams


async def teams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    match = get_match(chat_id)

    if match is None:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            parse_mode="markdown",
            text="Prima di iniziare con le danze, avvia una partita, per farlo usa /start",
        )
        return

    target = match.target
    reached_target = bool(match.participants) and match.confirmed_count == target

    if match.teams is not None:
        answer = format_teams(match.teams)
    else:
        if target % 2 != 0:
            answer = "Per usare questa funzionalità dovete essere in un numero pari di partecipanti"
        elif not reached_target:
            answer = f"Prima di poter fare le squadre, devi raggiungere {target} partecipanti"
        else:
            generated_teams = generate_teams(match.confirmed_names())
            save_teams(chat_id, generated_teams)
            answer = format_teams(generated_teams)

    await context.bot.send_message(
        chat_id=update.effective_chat.id, parse_mode="markdown", text=answer
    )
