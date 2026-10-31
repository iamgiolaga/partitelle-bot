"""The production logging setup (main.configure_logging) must never write the bot token (issue #130)."""

import logging
from contextlib import contextmanager

import httpx

from main import configure_logging

FAKE_TOKEN = "987654321:FAKE-token-that-must-never-be-logged"


class _Collector(logging.Handler):
    def __init__(self):
        super().__init__(level=logging.NOTSET)
        self.messages = []

    def emit(self, record):
        self.messages.append(self.format(record))


@contextmanager
def pristine_logging():
    """Logging as the bot finds it at startup (no root handlers), fully restored on exit.

    Used inside the test body: pytest attaches its own handlers to the root logger for each test phase,
    which would turn basicConfig into a no-op.
    """
    root = logging.getLogger()
    httpx_logger = logging.getLogger("httpx")
    saved_handlers, saved_level = root.handlers[:], root.level
    saved_httpx_level = httpx_logger.level
    root.handlers.clear()
    root.setLevel(logging.WARNING)
    httpx_logger.setLevel(logging.NOTSET)
    try:
        yield root
    finally:
        for handler in root.handlers:
            if handler not in saved_handlers:
                handler.close()
        root.handlers[:] = saved_handlers
        root.setLevel(saved_level)
        httpx_logger.setLevel(saved_httpx_level)


def test_bot_api_requests_do_not_log_the_token():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"ok": True, "result": {}})
    )
    with pristine_logging() as root:
        configure_logging()
        collector = _Collector()
        collector.setFormatter(root.handlers[0].formatter)
        root.addHandler(collector)

        with httpx.Client(transport=transport) as client:
            response = client.get(f"https://api.telegram.org/bot{FAKE_TOKEN}/getMe")
        # the setup records INFO messages, so the token check below is not vacuous
        logging.getLogger("main").info("probe")

        httpx_enabled_for_info = logging.getLogger("httpx").isEnabledFor(logging.INFO)
        root_level = root.level

    assert response.status_code == 200
    assert [message for message in collector.messages if FAKE_TOKEN in message] == []
    assert root_level == logging.INFO
    assert not httpx_enabled_for_info
    assert collector.messages[-1].endswith(" - main - INFO - probe")
