"""A fake Telegram world around the REAL python-telegram-bot Application (harness only).

The only things faked are the network edge (`FakeTelegram`, a `BaseRequest` that never leaves the process) and
the clock. Handlers, application and job queue are the real python-telegram-bot objects; the job queue is
never started, so jobs are only captured and run by `World.run_scheduled_jobs`.

The steps are synchronous: every coroutine runs on a dedicated event loop owned by the `World`.
"""

import asyncio
import json
import re
import time
import zlib
from dataclasses import dataclass, field

from telegram import Update
from telegram.ext import Application
from telegram.request import BaseRequest

BOT_ID = 424242
BOT_USERNAME = "partitelle_test_bot"
BOT_TOKEN = "123456:TEST"


def _snake(endpoint):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", endpoint).lower()


@dataclass
class Call:
    method: str
    params: dict

    def __str__(self):
        return f"{self.method}({self.params})"


@dataclass
class Chat:
    id: int
    title: str
    type: str = "group"

    def to_json(self):
        return {"id": self.id, "type": self.type, "title": self.title}


@dataclass
class Person:
    id: int
    first_name: str
    username: str = None
    last_name: str = None

    def to_json(self):
        data = {"id": self.id, "is_bot": False, "first_name": self.first_name}
        if self.last_name:
            data["last_name"] = self.last_name
        if self.username:
            data["username"] = self.username
        return data


class FakeTelegram(BaseRequest):
    """Records every outgoing Bot API call and answers with plausible Telegram payloads. No network."""

    def __init__(self, world):
        self.world = world
        self.calls = []
        self.sent_ids = []
        self.can_pin = True
        self.failures = {}  # method -> Telegram error descriptions to answer with, once each

    def fail_next(self, method, description):
        self.failures.setdefault(method, []).append(description)

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

    @property
    def read_timeout(self):
        return None

    @staticmethod
    def _reply(status, body):
        return status, json.dumps(body).encode()

    def _ok(self, result):
        return self._reply(200, {"ok": True, "result": result})

    def _bot_json(self):
        return {
            "id": BOT_ID,
            "is_bot": True,
            "first_name": "Partitelle",
            "username": BOT_USERNAME,
        }

    async def do_request(
        self,
        url,
        method,
        request_data=None,
        read_timeout=BaseRequest.DEFAULT_NONE,
        write_timeout=BaseRequest.DEFAULT_NONE,
        connect_timeout=BaseRequest.DEFAULT_NONE,
        pool_timeout=BaseRequest.DEFAULT_NONE,
    ):
        endpoint = url.rsplit("/", 1)[1]
        if endpoint == "getMe":  # Bot.initialize(), not part of the scenario
            return self._ok(self._bot_json())

        params = dict(request_data.parameters) if request_data else {}
        method = _snake(endpoint)
        self.calls.append(Call(method, params))

        if self.failures.get(method):
            return self._reply(
                400,
                {
                    "ok": False,
                    "error_code": 400,
                    "description": f"Bad Request: {self.failures[method].pop(0)}",
                },
            )

        if method in ("send_message", "edit_message_text"):
            chat = self.world.chats_by_id[int(params["chat_id"])]
            message_id = (
                self.world.next_message_id(chat.id)
                if method == "send_message"
                else int(params["message_id"])
            )
            if method == "send_message":
                self.sent_ids.append(message_id)
            return self._ok(
                {
                    "message_id": message_id,
                    "date": self.world.now_ts(),
                    "chat": chat.to_json(),
                    "from": self._bot_json(),
                    "text": params["text"],
                }
            )
        if method == "pin_chat_message":
            if not self.can_pin:
                return self._reply(
                    400,
                    {
                        "ok": False,
                        "error_code": 400,
                        "description": "Bad Request: not enough rights to pin a message",
                    },
                )
            return self._ok(True)
        if method in (
            "unpin_chat_message",
            "unpin_all_chat_messages",
            "delete_message",
        ):
            return self._ok(True)
        raise AssertionError(
            f"Network call attempted by the app, not supported by the fake Telegram: {method} {params}"
        )


@dataclass
class World:
    chats: dict = field(default_factory=dict)
    chats_by_id: dict = field(default_factory=dict)
    users: dict = field(default_factory=dict)
    current_chat: Chat = None
    consumed: int = 0
    consumed_warnings: int = 0  # logged warnings already asserted (see steps.py)
    errors: list = field(default_factory=list)
    _message_ids: dict = field(default_factory=dict)
    _update_id: int = 0
    clock: object = None
    texts: dict = field(
        default_factory=dict
    )  # named texts of the scenario (see steps.py)
    # a scenario declares an unhandled handler exception (see `the bot is expected to crash` in steps.py)
    expect_failures: bool = False

    def __post_init__(self):
        from handlers import (
            register_handlers,
        )  # imported late: env is set by test/conftest.py

        self.loop = asyncio.new_event_loop()
        self.telegram = FakeTelegram(self)
        self.application = (
            Application.builder()
            .token(BOT_TOKEN)
            .request(self.telegram)
            .get_updates_request(FakeTelegram(self))
            .updater(None)  # no polling/webhook: updates are fed by `send`
            .build()
        )
        # the job queue is never started: jobs are only captured, `run_scheduled_jobs` runs them
        self.job_queue = self.application.job_queue
        register_handlers(self.application)
        self.application.add_error_handler(self._record_error)
        self.run(self.application.initialize())

    async def _record_error(self, update, context):
        self.errors.append(context.error)

    def run(self, coroutine):
        return self.loop.run_until_complete(coroutine)

    def close(self):
        self.run(self.application.shutdown())
        self.loop.close()

    # ids and time -------------------------------------------------------------------------------
    def next_message_id(self, chat_id):
        self._message_ids[chat_id] = self._message_ids.get(chat_id, 0) + 1
        return self._message_ids[chat_id]

    def now_ts(self):
        return int(time.time())

    # actors -------------------------------------------------------------------------------------
    def add_chat(self, title):
        chat_id = -(1_000_000_000 + zlib.crc32(title.encode()) % 1_000_000)
        chat = Chat(chat_id, title)
        self.chats[title] = chat
        self.chats_by_id[chat_id] = chat
        self.current_chat = chat
        return chat

    def add_user(self, label, first_name, username, last_name=None):
        person = Person(1000 + len(self.users), first_name, username, last_name)
        self.users[label] = person
        return person

    # traffic ------------------------------------------------------------------------------------
    def send(self, label, text, chat=None, with_sender=True, edited=False):
        chat = chat or self.current_chat
        person = self.users[label]
        message = {
            "message_id": self.next_message_id(chat.id),
            "date": self.now_ts(),
            "chat": chat.to_json(),
            "from": person.to_json(),
            "text": text,
        }
        if not with_sender:
            del message["from"]
        if edited:  # the user edited one of their messages: Telegram sends an `edited_message` update
            message["edit_date"] = self.now_ts()
        if text.startswith("/"):
            command = text.split()[0]
            message["entities"] = [
                {"type": "bot_command", "offset": 0, "length": len(command)}
            ]
        self._update_id += 1
        update = Update.de_json(
            {
                "update_id": self._update_id,
                "edited_message" if edited else "message": message,
            },
            self.application.bot,
        )
        self.run(self.application.process_update(update))
        if self.errors and not self.expect_failures:
            raise self.errors[0]

    def run_scheduled_jobs(self):
        for job in self.job_queue.jobs():
            self.run(job.run(self.application))
        if self.errors and not self.expect_failures:
            raise self.errors[0]

    # assertions helpers -------------------------------------------------------------------------
    def next_call(self):
        if self.consumed >= len(self.telegram.calls):
            raise AssertionError(
                "Expected the bot to do something, but it did nothing more."
            )
        call = self.telegram.calls[self.consumed]
        self.consumed += 1
        return call

    def unconsumed(self):
        return self.telegram.calls[self.consumed :]

    def forget_calls(self):
        """Used by Given steps: setup traffic is not part of the scenario's expectations."""
        self.consumed = len(self.telegram.calls)

    def last_bot_message_id(self):
        if not self.telegram.sent_ids:
            raise AssertionError("The bot has not sent any message yet.")
        return self.telegram.sent_ids[-1]
