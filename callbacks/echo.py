from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from behaviours.edit_summary import edit_summary
from behaviours.print_new_summary import print_new_summary
from behaviours.remove_job_if_exists import remove_job_if_exists
from behaviours.trigger_payment_reminder import trigger_payment_reminder
from db.queries import (
    find_row_by_chat_id,
    find_all_info_by_chat_id,
    update_players_on_db,
    update_teams_on_db,
    is_already_present,
    update_bot_last_message_id_on_db,
)
from utils.utils import (
    parse_names,
    join_names,
    is_command_name,
    get_sender_name,
    confirmed_count,
    already_in_message,
    swap_players,
    parse_swap,
    format_summary,
)
from utils.constants import maybe_placeholder


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_message = update.message.text.lower()
    # the first word must be exactly the command: "aggiungimi pure" is just chat
    command = new_message.split(" ")[0]
    chat_id = update.message.chat_id
    answer = None
    show_summary = True
    reached_target = False
    revoked_teams = False
    answer_is_escaped = False
    command_name_answer = "Un nome non può iniziare con /"

    if (
        new_message in ["aggiungimi", "toglimi", "proponimi"]
        or command in ["aggiungi", "togli", "proponi"]
        or command == "scambia"
    ):
        row = find_row_by_chat_id(chat_id)
        if row is None:
            answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
            await context.bot.send_message(
                chat_id=update.effective_chat.id, parse_mode="markdown", text=answer
            )
        else:
            players, day, time, target, _, pitch, teams, bot_last_message_id = (
                find_all_info_by_chat_id(chat_id)
            )

            if new_message == "aggiungimi":
                sender = "@" + get_sender_name(update)
                if is_already_present(chat_id, sender):
                    answer = "Ma " + sender + ", sei già nella lista"
                    show_summary = False
                elif is_already_present(chat_id, sender + maybe_placeholder):
                    answer = "Ok, " + sender + ", ti confermo"
                    update_players_on_db(chat_id, sender + maybe_placeholder, "remove")
                    update_players_on_db(chat_id, sender, "add")
                    show_summary = True
                    reached_target = confirmed_count(players) + 1 == target
                else:
                    if len(players or []) < target:
                        answer = "Ok, " + sender + ", ti aggiungo"
                        update_players_on_db(chat_id, sender, "add")
                        show_summary = True
                        reached_target = confirmed_count(players) + 1 == target
                    else:
                        answer = already_in_message(players, target)
                        show_summary = False

            elif command == "aggiungi":
                names = parse_names(new_message[len(command) :])
                show_summary = False
                if not names:
                    answer = "Chi dovrei aggiungere? Scrivi: aggiungi <nome>"
                elif any(is_command_name(name) for name in names):
                    answer = command_name_answer
                else:
                    added, confirmed, present, full = [], [], [], []
                    for to_be_added in dict.fromkeys(names):
                        players = find_all_info_by_chat_id(chat_id)[0]
                        if is_already_present(chat_id, to_be_added):
                            present.append(to_be_added)
                            step_summary = False
                            step_reached = False
                        elif is_already_present(
                            chat_id, to_be_added + maybe_placeholder
                        ):
                            confirmed.append(to_be_added)
                            update_players_on_db(
                                chat_id, to_be_added + maybe_placeholder, "remove"
                            )
                            update_players_on_db(chat_id, to_be_added, "add")
                            step_summary = True
                            step_reached = confirmed_count(players) + 1 == target
                        elif len(players or []) < target:
                            added.append(to_be_added)
                            update_players_on_db(chat_id, to_be_added, "add")
                            step_summary = True
                            step_reached = confirmed_count(players) + 1 == target
                        else:
                            full.append(to_be_added)
                            step_summary = False
                            step_reached = False
                        show_summary = show_summary or step_summary
                        reached_target = reached_target or bool(step_reached)
                    sentences = []
                    if added:
                        sentences.append("Ok, aggiungo " + join_names(added))
                    if confirmed:
                        sentences.append(
                            "Ok, "
                            + join_names(confirmed)
                            + (
                                ", vi confermo"
                                if len(confirmed) > 1
                                else ", ti confermo"
                            )
                        )
                    if present:
                        sentences.append(
                            join_names(present)
                            + (
                                " sono già nella lista"
                                if len(present) > 1
                                else " è già nella lista"
                            )
                        )
                    if full:
                        if added or confirmed:
                            sentences.append(
                                "Ma aspetta! Non posso aggiungere "
                                + join_names(full)
                                + " perché siete già in "
                                + str(target)
                            )
                        else:
                            sentences.append(already_in_message(players, target))
                    answer = escape_markdown(". ".join(sentences))
                    answer_is_escaped = True

            elif new_message == "proponimi":
                sender = "@" + get_sender_name(update)
                if is_already_present(chat_id, sender + maybe_placeholder):
                    answer = "Ma " + sender + ", sei già in forse"
                    show_summary = False
                elif is_already_present(chat_id, sender):
                    answer = "Ok, " + sender + ", ti metto in forse"
                    update_players_on_db(chat_id, sender, "remove")
                    update_players_on_db(chat_id, sender + maybe_placeholder, "add")
                    show_summary = True
                    revoked_teams = teams is not None
                else:
                    if len(players or []) < target:
                        answer = "Ok, " + sender + ", ti propongo"
                        update_players_on_db(chat_id, sender + maybe_placeholder, "add")
                        show_summary = True
                        revoked_teams = teams is not None
                    else:
                        answer = already_in_message(players, target)
                        show_summary = False

            elif command == "proponi":
                names = parse_names(new_message[len(command) :])
                show_summary = False
                if not names:
                    answer = "Chi dovrei proporre? Scrivi: proponi <nome>"
                elif any(is_command_name(name) for name in names):
                    answer = command_name_answer
                else:
                    proposed, moved, present, full = [], [], [], []
                    for to_be_added in dict.fromkeys(names):
                        players = find_all_info_by_chat_id(chat_id)[0]
                        if is_already_present(chat_id, to_be_added + maybe_placeholder):
                            present.append(to_be_added)
                            step_summary = False
                            step_revoked = False
                        elif is_already_present(chat_id, to_be_added):
                            moved.append(to_be_added)
                            update_players_on_db(chat_id, to_be_added, "remove")
                            update_players_on_db(
                                chat_id, to_be_added + maybe_placeholder, "add"
                            )
                            step_summary = True
                            step_revoked = teams is not None
                        elif len(players or []) < target:
                            proposed.append(to_be_added)
                            update_players_on_db(
                                chat_id, to_be_added + maybe_placeholder, "add"
                            )
                            step_summary = True
                            step_revoked = teams is not None
                        else:
                            full.append(to_be_added)
                            step_summary = False
                            step_revoked = False
                        show_summary = show_summary or step_summary
                        revoked_teams = revoked_teams or step_revoked
                    sentences = []
                    if proposed:
                        sentences.append("Ok, propongo " + join_names(proposed))
                    if moved:
                        sentences.append("Va bene, metto in forse " + join_names(moved))
                    if present:
                        sentences.append(
                            join_names(present)
                            + (
                                " sono già nella lista"
                                if len(present) > 1
                                else " è già nella lista"
                            )
                        )
                    if full:
                        if proposed or moved:
                            sentences.append(
                                "Ma aspetta! Non posso proporre "
                                + join_names(full)
                                + " perché siete già in "
                                + str(target)
                            )
                        else:
                            sentences.append(already_in_message(players, target))
                    answer = escape_markdown(". ".join(sentences))
                    answer_is_escaped = True

            elif new_message == "toglimi":
                sender = "@" + get_sender_name(update)
                if is_already_present(chat_id, sender):
                    answer = "Mamma mia... che paccaro"
                    update_players_on_db(chat_id, sender, "remove")
                    show_summary = True
                    revoked_teams = teams is not None
                else:
                    if is_already_present(chat_id, sender + maybe_placeholder):
                        answer = "Peccato, un po' ci avevo sperato"
                        update_players_on_db(
                            chat_id, sender + maybe_placeholder, "remove"
                        )
                        show_summary = True
                        revoked_teams = teams is not None
                    else:
                        answer = "Non eri in lista neanche prima"
                        show_summary = False

            elif command == "togli":
                to_be_removed = new_message[len(command) :].strip()
                if not to_be_removed:
                    answer = "Chi dovrei togliere? Scrivi: togli <nome>"
                    show_summary = False
                elif is_command_name(to_be_removed):
                    answer = command_name_answer
                    show_summary = False
                elif is_already_present(chat_id, to_be_removed):
                    answer = "Che vergogna, " + to_be_removed
                    update_players_on_db(chat_id, to_be_removed, "remove")
                    show_summary = True
                    revoked_teams = teams is not None
                else:
                    if is_already_present(chat_id, to_be_removed + maybe_placeholder):
                        answer = (
                            "Davvero? Ma " + to_be_removed + ", ne sei proprio sicuro?"
                        )
                        update_players_on_db(
                            chat_id, to_be_removed + maybe_placeholder, "remove"
                        )
                        show_summary = True
                        revoked_teams = teams is not None
                    else:
                        answer = (
                            to_be_removed + " non è nella lista. Chi dovrei togliere?"
                        )
                        show_summary = False

            elif command == "scambia":
                show_summary = False
                names = parse_swap(new_message)
                if names is None:
                    answer = "Per scambiare due giocatori scrivi: scambia <nome 1> con <nome 2>"
                elif teams is None:
                    answer = "Per usare questa funzionalità devi prima formare delle squadre con /teams"
                else:
                    x, y = names
                    in_teams = teams["black"] + teams["white"]
                    if x not in in_teams:
                        answer = x + (
                            " non è in nessuna squadra"
                            if is_already_present(chat_id, x)
                            else " non c'è"
                        )
                    elif y not in in_teams:
                        answer = y + (
                            " non è in nessuna squadra"
                            if is_already_present(chat_id, y)
                            else " non c'è"
                        )
                    else:
                        try:
                            teams = swap_players(teams, x, y)
                            update_teams_on_db(chat_id, teams)
                            answer = "Perfetto, ho scambiato " + x + " con " + y
                        except ValueError:
                            answer = x + " e " + y + " sono nella stessa squadra!"

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                parse_mode="markdown",
                text=answer if answer_is_escaped else escape_markdown(answer),
            )

            if revoked_teams:
                update_teams_on_db(chat_id, None)
                remove_job_if_exists(str(chat_id), context)
                answer = "*SQUADRE ANNULLATE*"
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, parse_mode="markdown", text=answer
                )

            if show_summary:
                (
                    players,
                    day,
                    time,
                    target,
                    default_message,
                    pitch,
                    teams,
                    bot_last_message_id,
                ) = find_all_info_by_chat_id(chat_id)
                current_situation = format_summary(
                    players, day, time, target, default_message, pitch
                )
                if bot_last_message_id is None:
                    msg = await print_new_summary(current_situation, update, context)
                    update_bot_last_message_id_on_db(chat_id, msg.message_id)
                else:
                    await edit_summary(
                        current_situation, bot_last_message_id, update, context
                    )

                if reached_target:
                    trigger_payment_reminder(update, context, day, time)
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        parse_mode="markdown",
                        text="🚀 *SI GIOCA* 🚀 facciamo le squadre? /teams 😎",
                    )
