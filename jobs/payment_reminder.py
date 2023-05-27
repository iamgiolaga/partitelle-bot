from db.queries import update_bot_last_message_id_on_db

def payment_reminder(context):
    job = context.job
    chat_id = job.name

    msg = context.bot.send_message(chat_id, text="Ciao bestie 😎, com'è andata la partita? C'è qualcuno che non ha ancora pagato la sua quota?")

    try:
        context.bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id)
    except:
        print("No admin rights to pin the message")

    update_bot_last_message_id_on_db(chat_id, msg.message_id)
