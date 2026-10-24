from telegram.ext import CommandHandler, MessageHandler, Filters
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


def register_handlers(dispatcher):
    """Wire every command/message handler to the dispatcher (shared by main.py and the feature tests)."""
    start_handler = CommandHandler("start", start)
    dispatcher.add_handler(start_handler)

    set_number_handler = CommandHandler("setnumber", set_number)
    dispatcher.add_handler(set_number_handler)

    set_day_handler = CommandHandler("setday", set_day)
    dispatcher.add_handler(set_day_handler)

    set_time_handler = CommandHandler("settime", set_time)
    dispatcher.add_handler(set_time_handler)

    set_description_handler = CommandHandler("setdescription", set_description)
    dispatcher.add_handler(set_description_handler)

    set_pitch_handler = CommandHandler("setpitch", set_pitch)
    dispatcher.add_handler(set_pitch_handler)

    participants_handler = CommandHandler("participants", participants)
    dispatcher.add_handler(participants_handler)

    teams_handler = CommandHandler("teams", teams)
    dispatcher.add_handler(teams_handler)

    stop_handler = CommandHandler("stop", stop)
    dispatcher.add_handler(stop_handler)

    help_handler = CommandHandler("help", help_func)
    dispatcher.add_handler(help_handler)

    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    bamboo_handler = CommandHandler("bamboo", bamboo)
    dispatcher.add_handler(bamboo_handler)
