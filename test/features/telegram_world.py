"""A fake Telegram world around the REAL dispatcher wiring (harness only).

The only things faked are the network edge (`FakeBot._post`, nothing ever leaves the process) and the
clock/scheduler start. Handlers, dispatcher and job queue are the real python-telegram-bot objects.
"""

import re
import time
import warnings
import zlib
from queue import Queue
from dataclasses import dataclass, field

import telegram.error
from telegram import Bot, Update, User
from telegram.ext import Dispatcher, JobQueue

BOT_ID = 424242
BOT_USERNAME = "partitelle_test_bot"


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

    def to_json(self):
        data = {"id": self.id, "is_bot": False, "first_name": self.first_name}
        if self.username:
            data["username"] = self.username
        return data


class FakeBot(Bot):
    """Records every outgoing API call and answers with plausible Telegram payloads. No network."""

    def __init__(self, world):
        super().__init__(token="123456:TEST")
        self.world = world
        self._bot = User(BOT_ID, "Partitelle", True, username=BOT_USERNAME)
        self.calls = []
        self.sent_ids = []
        self.can_pin = True

    def _post(self, endpoint, data=None, timeout=None, api_kwargs=None):
        data = dict(data or {})
        data.update(api_kwargs or {})
        self._insert_defaults(data, timeout)
        params = {k: v for k, v in data.items() if v is not None}
        method = _snake(endpoint)
        self.calls.append(Call(method, params))

        if method in ("send_message", "edit_message_text"):
            chat = self.world.chats_by_id[int(params["chat_id"])]
            message_id = (
                self.world.next_message_id(chat.id)
                if method == "send_message"
                else int(params["message_id"])
            )
            if method == "send_message":
                self.sent_ids.append(message_id)
            return {
                "message_id": message_id,
                "date": self.world.now_ts(),
                "chat": chat.to_json(),
                "from": {
                    "id": BOT_ID,
                    "is_bot": True,
                    "first_name": "Partitelle",
                    "username": BOT_USERNAME,
                },
                "text": params["text"],
            }
        if method == "pin_chat_message":
            if not self.can_pin:
                raise telegram.error.BadRequest("Not enough rights to pin a message")
            return True
        if method in (
            "unpin_chat_message",
            "unpin_all_chat_messages",
            "delete_message",
        ):
            return True
        raise AssertionError(
            f"Network call attempted by the app, not supported by the fake bot: {method} {params}"
        )


@dataclass
class World:
    chats: dict = field(default_factory=dict)
    chats_by_id: dict = field(default_factory=dict)
    users: dict = field(default_factory=dict)
    current_chat: Chat = None
    consumed: int = 0
    errors: list = field(default_factory=list)
    _message_ids: dict = field(default_factory=dict)
    _update_id: int = 0
    clock: object = None
    texts: dict = field(default_factory=dict)  # named texts of the scenario (see steps.py)

    def __post_init__(self):
        from handlers import (
            register_handlers,
        )  # imported late: env is set by test/conftest.py

        self.bot = FakeBot(self)
        with (
            warnings.catch_warnings()
        ):  # "no worker threads": we process updates synchronously
            warnings.simplefilter("ignore")
            self.job_queue = JobQueue()
            self.dispatcher = Dispatcher(
                self.bot, Queue(), workers=0, job_queue=self.job_queue, use_context=True
            )
        self.job_queue.set_dispatcher(
            self.dispatcher
        )  # NOT started: jobs are only captured
        register_handlers(self.dispatcher)
        self.dispatcher.add_error_handler(
            lambda update, context: self.errors.append(context.error)
        )

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

    def add_user(self, label, first_name, username):
        person = Person(1000 + len(self.users), first_name, username)
        self.users[label] = person
        return person

    # traffic ------------------------------------------------------------------------------------
    def send(self, label, text, chat=None):
        chat = chat or self.current_chat
        person = self.users[label]
        message = {
            "message_id": self.next_message_id(chat.id),
            "date": self.now_ts(),
            "chat": chat.to_json(),
            "from": person.to_json(),
            "text": text,
        }
        if text.startswith("/"):
            command = text.split()[0]
            message["entities"] = [
                {"type": "bot_command", "offset": 0, "length": len(command)}
            ]
        self._update_id += 1
        update = Update.de_json(
            {"update_id": self._update_id, "message": message}, self.bot
        )
        self.dispatcher.process_update(update)
        if self.errors:
            raise self.errors[0]

    def run_scheduled_jobs(self):
        for job in self.job_queue.jobs():
            job.run(self.dispatcher)
        if self.errors:
            raise self.errors[0]

    # assertions helpers -------------------------------------------------------------------------
    def next_call(self):
        if self.consumed >= len(self.bot.calls):
            raise AssertionError(
                "Expected the bot to do something, but it did nothing more."
            )
        call = self.bot.calls[self.consumed]
        self.consumed += 1
        return call

    def unconsumed(self):
        return self.bot.calls[self.consumed :]

    def forget_calls(self):
        """Used by Given steps: setup traffic is not part of the scenario's expectations."""
        self.consumed = len(self.bot.calls)

    def last_bot_message_id(self):
        if not self.bot.sent_ids:
            raise AssertionError("The bot has not sent any message yet.")
        return self.bot.sent_ids[-1]
