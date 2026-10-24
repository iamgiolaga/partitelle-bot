"""Paths the Gherkin scenarios do not describe (/bamboo, Telegram rejecting a summary), exercised through the same
fake Telegram world. Plain pytest on purpose: the .feature files are the contract and are not touched."""

from telegram.helpers import escape_markdown

BAMBOO_GREETING = "Ciao bestie 😎, chi c'è per il prossimo calcetto? \n"
SPECIAL_CHARACTER_HELP = (
    "Sembra che tu abbia inserito nella descrizione un carattere speciale di telegram (`, *, _).\n"
    "Per favore cambiala con /setdescription <descrizione> assicurandoti di non inserire uno di questi caratteri.\n"
    "Se la tua intenzione era, invece, di formattare il testo, ricordati di usare anche il carattere di chiusura, come in questo *esempio*."
)


def test_bamboo_creates_the_match_with_the_bamboo_defaults_once(world):
    world.add_chat("Bamboo")
    world.add_user("@giulia", "Giulia", "giulia")

    world.send("@giulia", "/bamboo")

    greeting = world.next_call()
    assert greeting.method == "send_message"
    assert greeting.params["parse_mode"] == "markdown"
    assert greeting.params["text"].startswith(BAMBOO_GREETING)
    match = world.db.fetch_match(world.current_chat.id)
    assert match["pitch"].startswith("Crespi Sport Village")
    assert match["day"].startswith("Mercoledì ")

    world.db.conn.execute(
        f"UPDATE {world.db.table} SET pitch = 'Altro campo' WHERE chat_id = %s",
        [world.current_chat.id],
    )
    world.send("@giulia", "/bamboo")  # already there: answered, not recreated
    assert world.next_call().method == "send_message"
    assert world.db.fetch_match(world.current_chat.id)["pitch"] == "Altro campo"
    assert not world.unconsumed()


def test_summary_rejected_by_telegram_is_replaced_by_the_special_character_help(world):
    world.add_chat("Calcetto")
    world.add_user("@giulia", "Giulia", "giulia")
    world.send("@giulia", "/start")
    world.forget_calls()
    world.telegram.fail_next("send_message", "can't parse entities")

    world.send("@giulia", "/participants")

    rejected, help_message = world.next_call(), world.next_call()
    assert rejected.params["text"].startswith("*GIORNO*")
    assert help_message.method == "send_message"
    assert help_message.params["text"] == escape_markdown(SPECIAL_CHARACTER_HELP)
    assert not world.unconsumed()  # nothing to pin


def test_summary_edit_survives_the_bot_not_being_admin(world):
    world.add_chat("Calcetto")
    world.add_user("@giulia", "Giulia", "giulia")
    world.send("@giulia", "/start")
    world.send("@giulia", "/participants")  # tracks a summary message
    world.telegram.can_pin = False
    world.forget_calls()

    world.send("@giulia", "setpitch")  # plain text, ignored
    world.send("@giulia", "/setpitch Campo Nuovo")

    methods = [call.method for call in world.unconsumed()]
    assert methods == ["send_message", "edit_message_text", "pin_chat_message"]
