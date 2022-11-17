from telegram import Update
from telegram.ext import CallbackContext
from db.queries import find_all_info_by_chat_id, update_teams_on_db
from utils.behaviours import filter_maybe_placeholders, print_teams, generate_teams
import json

def teams(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_all_info_by_chat_id(chat_id)

    if row is None:
        answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
        context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)

    else:
        players = row[0]
        target = row[3]
        teams = row[-2]
        if players is None:
            participants_num = 0
        else:
            participants_num = len(filter_maybe_placeholders(players))
        reached_target = players and participants_num == target

        if teams is not None:
            print_teams(json.dumps(teams), update, context)
        else:
            if target % 2 == 0:
                if not reached_target:
                    answer = "Prima di poter fare le squadre, devi raggiungere " + str(target) + " partecipanti"
                    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)
                else:
                    generated_teams = generate_teams(players)
                    update_teams_on_db(chat_id, generated_teams)
                    print_teams(generated_teams, update, context)
            else:
                answer = "Per usare questa funzionalità dovete essere in un numero pari di partecipanti"
                context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown', text=answer)