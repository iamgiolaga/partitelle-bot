from telegram import Update
from telegram.ext import CallbackContext
from db.queries import find_all_info_by_chat_id, create_chat_id_row

def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    row = find_all_info_by_chat_id(chat_id)

    if row is None:
        create_chat_id_row(chat_id)

    context.bot.send_message(chat_id=update.effective_chat.id, parse_mode='markdown',
                             text="Ciao bestie 😎, chi c'è per il prossimo calcetto? \n"
                                  "\n"
                                  "- se sei in forse scrivi _proponimi_, \n" \
                                  "- se vuoi proporre qualcuno scrivi _proponi <nome>_, \n" \
                                  "- per essere aggiunto o confermato rispondi _aggiungimi_,\n" \
                                  "- per aggiungere o confermare qualcuno usa _aggiungi <nome>_,\n" \
                                  "- per essere rimosso _toglimi_, \n" \
                                  "- per rimuovere qualcuno _togli <nome>_, \n" \
                                  "- per modificare le squadre scrivi _scambia <nome 1> con <nome 2>_. \n\n" \
                                  "Posso anche pinnare i messaggi se vuoi " \
                                  "ma per farlo ricordati di aggiungermi come amministratore."
                             )
