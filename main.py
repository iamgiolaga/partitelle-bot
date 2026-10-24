from telegram.ext import Updater
from conf.conf import token, hosting_url, env
from handlers import register_handlers
import logging
import os

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

if __name__ == "__main__":
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher

    register_handlers(dispatcher)

    if env == "local":
        updater.start_polling()
    else:
        updater.start_webhook(
            listen="0.0.0.0",
            webhook_url=f"{hosting_url}/{token}",
            url_path=token,
            port=int(os.environ.get("PORT", 5000)),
        )
        updater.idle()
