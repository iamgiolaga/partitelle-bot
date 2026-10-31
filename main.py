import hashlib
import logging
import os

from telegram.ext import Application, ContextTypes

from conf.conf import token, hosting_url, env, webhook_secret
from handlers import register_handlers

logger = logging.getLogger(__name__)

WEBHOOK_PATH = "telegram"


def compute_webhook_secret(bot_token, configured_secret=None):
    """Secret Telegram sends back in X-Telegram-Bot-Api-Secret-Token (allowed: [A-Za-z0-9_-], 1-256 chars).

    `PB_WEBHOOK_SECRET` when set, otherwise derived deterministically from the bot token, so no extra
    configuration is needed and the secret is stable across restarts and deploys.
    """
    if configured_secret:
        return configured_secret
    return hashlib.sha256(bot_token.encode()).hexdigest()


async def log_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log every unhandled handler/job exception. Users see nothing, as it has always been."""
    logger.error("Exception while handling an update:", exc_info=context.error)


def build_application(bot_token=token):
    application = Application.builder().token(bot_token).build()
    register_handlers(application)
    application.add_error_handler(log_error)
    return application


def configure_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    # httpx logs every request URL at INFO, and Bot API URLs contain the bot token (/bot<token>/...).
    logging.getLogger("httpx").setLevel(logging.WARNING)


def main():
    configure_logging()
    application = build_application()

    if env == "local":
        application.run_polling()
    else:
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 5000)),
            url_path=WEBHOOK_PATH,
            webhook_url=f"{hosting_url}/{WEBHOOK_PATH}",
            secret_token=compute_webhook_secret(token, webhook_secret),
        )


if __name__ == "__main__":
    main()
