from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from behaviours.edit_summary import edit_summary
from behaviours.print_new_summary import print_new_summary
from behaviours.remove_job_if_exists import remove_job_if_exists
from behaviours.trigger_payment_reminder import trigger_payment_reminder
from db.repository import (
    add_participant,
    get_match,
    remove_participant,
    save_teams,
    set_participant_maybe,
    set_summary_message_id,
)
from domain import Participant
from utils.utils import (
    parse_names,
    join_names,
    is_command_name,
    already_in_message,
    get_sender_mention,
    swap_players,
    parse_swap,
    format_summary,
)


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

    is_self_action = new_message in ["aggiungimi", "toglimi", "proponimi"]
    sender = get_sender_mention(update) if is_self_action else None
    if is_self_action and sender is None:
        # the sender cannot be retrieved (issue #25): nobody to add, propose or remove
        return

    if (
        is_self_action
        or command in ["aggiungi", "togli", "proponi"]
        or command == "scambia"
    ):
        match = get_match(chat_id)
        if match is None:
            answer = "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
            await context.bot.send_message(
                chat_id=update.effective_chat.id, parse_mode="markdown", text=answer
            )
        else:
            # target and teams are read once per message; the participants are re-read
            # per name by the commands that take several
            target = match.target
            teams = match.teams

            if new_message == "aggiungimi":
                if match.find(sender, False):
                    answer = "Ma " + sender + ", sei già nella lista"
                    show_summary = False
                elif match.find(sender, True):
                    answer = "Ok, " + sender + ", ti confermo"
                    set_participant_maybe(chat_id, sender, False)
                    show_summary = True
                    reached_target = match.confirmed_count + 1 == target
                else:
                    if match.has_room:
                        answer = "Ok, " + sender + ", ti aggiungo"
                        add_participant(chat_id, Participant(sender))
                        show_summary = True
                        reached_target = match.confirmed_count + 1 == target
                    else:
                        answer = already_in_message(match)
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
                        current = get_match(chat_id)
                        if current.find(to_be_added, False):
                            present.append(to_be_added)
                            step_summary = False
                            step_reached = False
                        elif current.find(to_be_added, True):
                            confirmed.append(to_be_added)
                            set_participant_maybe(chat_id, to_be_added, False)
                            step_summary = True
                            step_reached = current.confirmed_count + 1 == target
                        elif len(current.participants) < target:
                            added.append(to_be_added)
                            add_participant(chat_id, Participant(to_be_added))
                            step_summary = True
                            step_reached = current.confirmed_count + 1 == target
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
                            sentences.append(already_in_message(current))
                    answer = escape_markdown(". ".join(sentences))
                    answer_is_escaped = True

            elif new_message == "proponimi":
                if match.find(sender, True):
                    answer = "Ma " + sender + ", sei già in forse"
                    show_summary = False
                elif match.find(sender, False):
                    answer = "Ok, " + sender + ", ti metto in forse"
                    set_participant_maybe(chat_id, sender, True)
                    show_summary = True
                    revoked_teams = teams is not None
                else:
                    if match.has_room:
                        answer = "Ok, " + sender + ", ti propongo"
                        add_participant(chat_id, Participant(sender, True))
                        show_summary = True
                        revoked_teams = teams is not None
                    else:
                        answer = already_in_message(match)
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
                        current = get_match(chat_id)
                        if current.find(to_be_added, True):
                            present.append(to_be_added)
                            step_summary = False
                            step_revoked = False
                        elif current.find(to_be_added, False):
                            moved.append(to_be_added)
                            set_participant_maybe(chat_id, to_be_added, True)
                            step_summary = True
                            step_revoked = teams is not None
                        elif len(current.participants) < target:
                            proposed.append(to_be_added)
                            add_participant(chat_id, Participant(to_be_added, True))
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
                            sentences.append(already_in_message(current))
                    answer = escape_markdown(". ".join(sentences))
                    answer_is_escaped = True

            elif new_message == "toglimi":
                if match.find(sender, False):
                    answer = "Mamma mia... che paccaro"
                    remove_participant(chat_id, Participant(sender))
                    show_summary = True
                    revoked_teams = teams is not None
                else:
                    if match.find(sender, True):
                        answer = "Peccato, un po' ci avevo sperato"
                        remove_participant(chat_id, Participant(sender, True))
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
                elif match.find(to_be_removed, False):
                    answer = "Che vergogna, " + to_be_removed
                    remove_participant(chat_id, Participant(to_be_removed))
                    show_summary = True
                    revoked_teams = teams is not None
                else:
                    if match.find(to_be_removed, True):
                        answer = (
                            "Davvero? Ma " + to_be_removed + ", ne sei proprio sicuro?"
                        )
                        remove_participant(chat_id, Participant(to_be_removed, True))
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
                    if not teams.contains(x):
                        answer = x + (
                            " non è in nessuna squadra"
                            if match.find(x, False)
                            else " non c'è"
                        )
                    elif not teams.contains(y):
                        answer = y + (
                            " non è in nessuna squadra"
                            if match.find(y, False)
                            else " non c'è"
                        )
                    else:
                        try:
                            teams = swap_players(teams, x, y)
                            save_teams(chat_id, teams)
                            answer = "Perfetto, ho scambiato " + x + " con " + y
                        except ValueError:
                            answer = x + " e " + y + " sono nella stessa squadra!"

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                parse_mode="markdown",
                text=answer if answer_is_escaped else escape_markdown(answer),
            )

            if revoked_teams:
                save_teams(chat_id, None)
                remove_job_if_exists(str(chat_id), context)
                answer = "*SQUADRE ANNULLATE*"
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, parse_mode="markdown", text=answer
                )

            if show_summary:
                current = get_match(chat_id)
                current_situation = format_summary(current)
                if current.summary_message_id is None:
                    msg = await print_new_summary(current_situation, update, context)
                    set_summary_message_id(chat_id, msg.message_id)
                else:
                    await edit_summary(
                        current_situation, current.summary_message_id, update, context
                    )

                if reached_target:
                    trigger_payment_reminder(update, context, current.starts)
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        parse_mode="markdown",
                        text="🚀 *SI GIOCA* 🚀 facciamo le squadre? /teams 😎",
                    )
