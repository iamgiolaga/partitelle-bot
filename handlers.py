from telegram.ext import CommandHandler, MessageHandler, filters
from callbacks.start import start
from callbacks.stop import stop
from callbacks.set_number import set_number
from callbacks.set_time import set_time
from callbacks.set_day import set_day
from callbacks.set_pitch import set_pitch
from callbacks.set_description import set_description
from callbacks.participants import participants
from callbacks.teams import teams
from callbacks.help_func import help_func
from callbacks.echo import echo
from callbacks.bamboo import bamboo

# Only new messages: edited messages also reach the handlers by default, but they come without
# `update.message`, which every callback reads (issue #25).
NEW_MESSAGES = filters.UpdateType.MESSAGE


def register_handlers(application):
    """Wire every command/message handler to the application (shared by main.py and the feature tests)."""
    start_handler = CommandHandler("start", start, filters=NEW_MESSAGES)
    application.add_handler(start_handler)

    set_number_handler = CommandHandler("setnumber", set_number, filters=NEW_MESSAGES)
    application.add_handler(set_number_handler)

    set_day_handler = CommandHandler("setday", set_day, filters=NEW_MESSAGES)
    application.add_handler(set_day_handler)

    set_time_handler = CommandHandler("settime", set_time, filters=NEW_MESSAGES)
    application.add_handler(set_time_handler)

    set_description_handler = CommandHandler(
        "setdescription", set_description, filters=NEW_MESSAGES
    )
    application.add_handler(set_description_handler)

    set_pitch_handler = CommandHandler("setpitch", set_pitch, filters=NEW_MESSAGES)
    application.add_handler(set_pitch_handler)

    participants_handler = CommandHandler(
        "participants", participants, filters=NEW_MESSAGES
    )
    application.add_handler(participants_handler)

    teams_handler = CommandHandler("teams", teams, filters=NEW_MESSAGES)
    application.add_handler(teams_handler)

    stop_handler = CommandHandler("stop", stop, filters=NEW_MESSAGES)
    application.add_handler(stop_handler)

    help_handler = CommandHandler("help", help_func, filters=NEW_MESSAGES)
    application.add_handler(help_handler)

    echo_handler = MessageHandler(filters.TEXT & ~filters.COMMAND & NEW_MESSAGES, echo)
    application.add_handler(echo_handler)

    bamboo_handler = CommandHandler("bamboo", bamboo, filters=NEW_MESSAGES)
    application.add_handler(bamboo_handler)
