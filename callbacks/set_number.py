from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from behaviours.edit_summary import edit_summary
from behaviours.print_new_summary import print_new_summary
from behaviours.remove_job_if_exists import remove_job_if_exists
from behaviours.trigger_payment_reminder import trigger_payment_reminder
from db.repository import set_target, set_summary_message_id
from db.repository import get_match, save_teams
from domain import TargetTooLow
from utils.utils import get_sender_mention, format_summary


def target_too_low_answer(refusal: TargetTooLow, current_target: int) -> str:
    advice = (
        "Prima togli qualcuno con togli <nome>, oppure lascia il numero a "
        f"{current_target} 🙏"
    )
    if refusal.maybe == 0:
        return (
            f"Non posso scendere a {refusal.requested}: "
            f"ci sono già {refusal.confirmed} confermati. {advice}"
        )
    maybes = f"{refusal.maybe} in forse"
    if refusal.confirmed == 0:
        counts = maybes
    elif refusal.confirmed == 1:
        counts = f"1 confermato e {maybes}"
    else:
        counts = f"{refusal.confirmed} confermati e {maybes}"
    return (
        f"Non posso scendere a {refusal.requested}: "
        f"in lista ci sono già {refusal.total} persone ({counts}), "
        f"e anche chi è in forse tiene un posto. {advice}"
    )


async def set_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    match = get_match(chat_id)

    if match is None:
        answer = (
            "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
        )
    else:
        try:
            if len(context.args) > 1:
                answer = (
                    "Hai messo più di un numero, probabilmente intendevi /setnumber "
                    + context.args[0]
                )
            else:
                chosen_number_str = context.args[0]
                sender = get_sender_mention(update)
                participants_num = match.confirmed_count

                if chosen_number_str.isnumeric():
                    chosen_number = int(chosen_number_str)
                    if chosen_number <= 0 or chosen_number > 40:
                        answer = "Non è un numero valido di partecipanti 🌚"
                    elif chosen_number < 2:
                        answer = "Il numero che hai inserito non va bene 👎"
                    elif (refusal := match.check_new_target(chosen_number)) is not None:
                        answer = target_too_low_answer(refusal, match.target)
                    else:
                        if match.teams is not None:
                            save_teams(chat_id, None)
                            remove_job_if_exists(str(chat_id), context)
                            answer = "*SQUADRE ANNULLATE*"
                            await context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                parse_mode="markdown",
                                text=answer,
                            )

                        set_target(chat_id, chosen_number)
                        answer = (
                            "Ok, "
                            + sender
                            + "! Ho impostato il numero di partecipanti a "
                            + str(chosen_number)
                        )
                        reached_target = (
                            bool(match.participants)
                            and participants_num == chosen_number
                        )
                        match = get_match(chat_id)
                        current_situation = format_summary(match)
                        if match.summary_message_id is None:
                            msg = await print_new_summary(
                                current_situation, update, context
                            )
                            set_summary_message_id(chat_id, msg.message_id)
                        else:
                            await edit_summary(
                                current_situation,
                                match.summary_message_id,
                                update,
                                context,
                            )

                        if reached_target:
                            trigger_payment_reminder(update, context, match.starts)
                            await context.bot.send_message(
                                chat_id=update.effective_chat.id,
                                parse_mode="markdown",
                                text="🚀 *SI GIOCA* 🚀 facciamo le squadre? /teams 😎",
                            )
                else:
                    answer = sender + ", quello ti sembra un numero? 😂"

        except Exception:
            answer = "Non hai inserito il numero: scrivi /setnumber <numero>"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        parse_mode="markdown",
        text=escape_markdown(answer),
    )
