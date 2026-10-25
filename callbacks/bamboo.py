from telegram import Update
from telegram.ext import ContextTypes
from db.repository import get_match, create_match
from domain import BAMBOO_PITCH, Match
from utils.utils import default_match_day


async def bamboo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if get_match(chat_id) is None:
        create_match(Match.new(chat_id, default_match_day(), BAMBOO_PITCH))

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        parse_mode="markdown",
        text="Ciao bestie 😎, chi c'è per il prossimo calcetto? \n"
        "\n"
        "- se sei in forse scrivi _proponimi_, \n"
        "- se vuoi proporre qualcuno scrivi _proponi <nome>_, \n"
        "- per essere aggiunto o confermato rispondi _aggiungimi_,\n"
        "- per aggiungere o confermare qualcuno usa _aggiungi <nome>_,\n"
        "- per essere rimosso _toglimi_, \n"
        "- per rimuovere qualcuno _togli <nome>_, \n"
        "- per modificare le squadre scrivi _scambia <nome 1> con <nome 2>_. \n\n"
        "Posso anche pinnare i messaggi se vuoi "
        "ma per farlo ricordati di aggiungermi come amministratore.",
    )
