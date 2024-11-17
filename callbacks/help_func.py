from telegram import Update
from telegram.ext import CallbackContext


def help_func(update: Update, context: CallbackContext):
    answer = (
        "Ecco a te la lista completa dei comandi di questo bot: \n"
        "- se sei in forse scrivi _proponimi_, \n"
        "- se vuoi proporre qualcuno scrivi _proponi <nome>_, \n"
        "- per essere aggiunto o confermato rispondi _aggiungimi_,\n"
        "- per aggiungere o confermare qualcuno usa _aggiungi <nome>_,\n"
        "- per essere rimosso _toglimi_, \n"
        "- per rimuovere qualcuno _togli <nome>_, \n"
        "- per modificare le squadre scrivi _scambia <nome 1> con <nome 2>_. \n\n"
        "Posso anche pinnare i messaggi se vuoi "
        "ma per farlo ricordati di aggiungermi come amministratore.\n"
        "\n"
        "/start - Crea una nuova partita \n"
        "/setnumber - Imposta il numero di partecipanti \n"
        "/setday - Imposta il giorno della partita \n"
        "/settime - Imposta l’orario della partita \n"
        "/setdescription - Imposta la descrizione sotto i partecipanti \n"
        "/setpitch - Imposta il campo \n"
        "/participants - Mostra i partecipanti della partita attuale \n"
        "/teams - Mostra le squadre della partita attuale \n"
        "/stop - Rimuovi la partita \n"
        "/help - Mostra la lista di comandi disponibili"
    )

    context.bot.send_message(
        chat_id=update.effective_chat.id, parse_mode="markdown", text=answer
    )
