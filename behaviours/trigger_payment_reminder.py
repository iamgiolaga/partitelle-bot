from jobs.payment_reminder import payment_reminder
from utils.utils import extract_match_time, extract_match_day, compute_seconds_from_now


def trigger_payment_reminder(update, context, day, time):
    chat_id = update.effective_message.chat_id
    match_time = extract_match_time(time)
    reminder_time_from_now = -1

    if match_time == -1:
        match_date = extract_match_day(day)
        waiting_time_in_seconds = 36 * 3600
    else:
        match_date = extract_match_day(f"{day} {time}")
        waiting_time_in_seconds = 2 * 3600

    if match_date != -1:
        reminder_time_from_now = (
            compute_seconds_from_now(match_date) + waiting_time_in_seconds
        )

    if reminder_time_from_now > 0:
        context.job_queue.run_once(
            payment_reminder, reminder_time_from_now, context=context, name=str(chat_id)
        )
