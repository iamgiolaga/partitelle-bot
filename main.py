from telegram.ext import CommandHandler, MessageHandler, Filters, Updater
from db.connection import connect
from utils.constants import token, hosting_url
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
import logging
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

if __name__ == '__main__':
    connection = connect()

    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    set_number_handler = CommandHandler('setnumber', set_number)
    dispatcher.add_handler(set_number_handler)

    set_day_handler = CommandHandler('setday', set_day)
    dispatcher.add_handler(set_day_handler)

    set_time_handler = CommandHandler('settime', set_time)
    dispatcher.add_handler(set_time_handler)

    set_description_handler = CommandHandler('setdescription', set_description)
    dispatcher.add_handler(set_description_handler)

    set_pitch_handler = CommandHandler('setpitch', set_pitch)
    dispatcher.add_handler(set_pitch_handler)

    participants_handler = CommandHandler('participants', participants)
    dispatcher.add_handler(participants_handler)

    teams_handler = CommandHandler('teams', teams)
    dispatcher.add_handler(teams_handler)

    stop_handler = CommandHandler('stop', stop)
    dispatcher.add_handler(stop_handler)

    help_handler = CommandHandler('help', help_func)
    dispatcher.add_handler(help_handler)

    echo_handler = MessageHandler(Filters.text & (~Filters.command), echo)
    dispatcher.add_handler(echo_handler)

    bamboo_handler = CommandHandler('bamboo', bamboo)
    dispatcher.add_handler(bamboo_handler)

    #updater.start_polling()
    updater.start_webhook(listen="0.0.0.0", webhook_url=f'{hosting_url}/{token}', url_path=token, port=int(os.environ.get('PORT', 5000)))
    updater.idle()
