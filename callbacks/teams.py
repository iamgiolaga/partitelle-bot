from telegram import Update
from telegram.ext import CallbackContext
from db.queries import find_all_info_by_chat_id, update_teams_on_db
from utils.utils import exclude_maybe, format_teams, generate_teams
import json


def teams(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_all_info_by_chat_id(chat_id)

    if row is None:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            parse_mode="markdown",
            text="Prima di iniziare con le danze, avvia una partita, per farlo usa /start",
        )
        return

    players, _, _, target, _, _, teams, _ = row
    participants_num = len(exclude_maybe(players)) if players else 0
    reached_target = players and participants_num == target

    if teams is not None:
        answer = format_teams(json.dumps(teams))
    else:
        if target % 2 != 0:
            answer = "Per usare questa funzionalità dovete essere in un numero pari di partecipanti"
        elif not reached_target:
            answer = f"Prima di poter fare le squadre, devi raggiungere {target} partecipanti"
        else:
            generated_teams = generate_teams(players)
            update_teams_on_db(chat_id, generated_teams)
            answer = format_teams(generated_teams)

    context.bot.send_message(
        chat_id=update.effective_chat.id, parse_mode="markdown", text=answer
    )
