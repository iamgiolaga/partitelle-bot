from datetime import datetime

from jobs.payment_reminder import payment_reminder
from utils.utils import compute_seconds_from_now

# the reminder asks how the match went, so it goes out after the match is over
REMINDER_DELAY_SECONDS = 2 * 3600


def trigger_payment_reminder(update, context, starts: datetime):
    chat_id = update.effective_message.chat_id
    reminder_time_from_now = compute_seconds_from_now(starts) + REMINDER_DELAY_SECONDS

    if reminder_time_from_now > 0:
        context.job_queue.run_once(
            payment_reminder, reminder_time_from_now, name=str(chat_id)
        )
