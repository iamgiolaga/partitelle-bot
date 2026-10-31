"""Step definitions. Wording is behaviour-level; everything PTB/DB specific lives behind `world`."""

import logging
import re
import random

from pytest_bdd import given, parsers, then, when

HEADER = ["field", "value"]
NONE = "(none)"

# ---- Named texts ------------------------------------------------------------------------------------
# `Given the text "welcome" is:` defines a text (in a Background: for the whole file); any docstring
# used by a Then-step can then contain `{welcome}`. Pure string substitution: the comparison stays exact.

PLACEHOLDER_RE = re.compile(r"\{([a-z0-9][a-z0-9 _-]*)\}")


def interpolate(world, text):
    """Replaces every `{name}` with the named text; other braces stay literal."""

    def _replace(found):
        name = found.group(1)
        if name not in world.texts:
            defined = ", ".join(sorted(world.texts)) or "(none)"
            raise AssertionError(
                f"Undefined text placeholder {{{name}}}. Defined texts: {defined}. "
                'Define it with: Given the text "<name>" is:'
            )
        return world.texts[name]

    return PLACEHOLDER_RE.sub(_replace, text)


# ---- Given -----------------------------------------------------------------------------------------


@given(parsers.parse('the text "{name}" is:'))
def _define_text(world, name, docstring):
    """Names a text for this scenario; it may use the texts defined before it."""
    world.texts[name] = interpolate(world, docstring)


@given(parsers.parse('a group chat "{title}"'))
def _group_chat(world, title):
    world.add_chat(title)


@given(parsers.re(r'the user "@(?P<username>[^"]+)"$'))
def _user_with_username(world, username):
    world.add_user("@" + username, username.capitalize(), username)


@given(parsers.re(r'a user named "(?P<name>[^"]+)" without username$'))
def _user_without_username(world, name):
    world.add_user(name, name, None)


@given(
    parsers.re(r'a user named "(?P<first>[^"]+)" "(?P<last>[^"]+)" without username$')
)
def _user_with_last_name_without_username(world, first, last):
    world.add_user(f"{first} {last}", first, None, last)


@given(parsers.parse('today is "{when}"'))
def _today(freeze_time, when):
    """Freezes the clock at `when` (YYYY-MM-DD HH:MM, Europe/Rome)."""
    freeze_time(when)


@given(parsers.parse('the clock moves to "{when}"'))
def _clock_moves(world, freeze_time, when):
    """Re-freezes the clock (YYYY-MM-DD HH:MM, Europe/Rome) after `today is` was already used."""
    if world.clock is not None:
        world.clock.stop()
        world.clock = None
    freeze_time(when)


@given(parsers.parse("the team draw is seeded with {seed:d}"))
def _seed_team_draw(request, seed):
    """Makes the random team draw deterministic: seeds Python's `random` and restores it afterwards."""
    previous = random.getstate()
    request.addfinalizer(lambda: random.setstate(previous))
    random.seed(seed)


@given(parsers.parse('the current chat is "{title}"'))
@then(parsers.parse('the current chat is "{title}"'))
def _current_chat(world, title):
    """Switches the chat the following steps and assertions refer to."""
    world.current_chat = world.chats[title]


@given(parsers.re(r'"(?P<who>[^"]+)" had sent "(?P<text>[^"]*)"$'))
def _had_sent(world, who, text):
    """Setup traffic: the message is really processed, but the bot's answers are not part of the expectations."""
    world.send(who, text)
    world.forget_calls()


@given(
    parsers.re(r'"(?P<who>[^"]+)" had sent "(?P<text>[^"]*)" in "(?P<title>[^"]+)"$')
)
def _had_sent_in(world, who, text, title):
    world.send(who, text, chat=world.chats[title])
    world.forget_calls()


@given(parsers.parse("the match target is {target:d}"))
def _match_target(world, target):
    world.db.set_target(world.current_chat.id, target)


@given(parsers.parse('the chat has the default pitch "{pitch}"'))
def _chat_default_pitch(world, pitch):
    """The chat was set up before: its setting row holds a pitch for every new match."""
    world.db.set_default_pitch(world.current_chat.id, pitch)


@given(parsers.parse('the match has the players "{players}"'))
def _match_players(world, players):
    """Comma separated, in order; a trailing ` (maybe)` marks a player who is only maybe present."""
    parsed = []
    for player in (p.strip() for p in players.split(",")):
        is_maybe = player.endswith(" (maybe)")
        parsed.append((player[: -len(" (maybe)")] if is_maybe else player, is_maybe))
    world.db.set_players(world.current_chat.id, parsed)


@given(
    parsers.parse('the match has the black team "{black}" and the white team "{white}"')
)
def _match_teams(world, black, white):
    world.db.set_teams(
        world.current_chat.id,
        [p.strip() for p in black.split(",")],
        [p.strip() for p in white.split(",")],
    )


@given("the bot is expected to crash on the next message")
def _expect_crash(world):
    """Handler exceptions are part of the scenario: they are recorded (not re-raised) and each one must
    be asserted with `Then the bot should fail with "<ExceptionType>"`."""
    world.expect_failures = True


@given("a match was started")
def _match_was_started(world):
    if not world.users:
        world.add_user("@organizer", "Organizer", "organizer")
    world.send(next(iter(world.users)), "/start")
    world.forget_calls()


@given("the bot is not an administrator of the chat")
def _bot_not_admin(world):
    world.telegram.can_pin = False


# ---- When ------------------------------------------------------------------------------------------


@when(parsers.re(r'"(?P<who>[^"]+)" sends "(?P<text>[^"]*)"$'))
def _sends(world, who, text):
    world.send(who, text)


@when(parsers.re(r'"(?P<who>[^"]+)" sends "(?P<text>[^"]*)" in "(?P<title>[^"]+)"$'))
def _sends_in(world, who, text, title):
    world.send(who, text, chat=world.chats[title])


@when(
    parsers.re(
        r'"(?P<who>[^"]+)" sends "(?P<text>[^"]*)" and the bot cannot retrieve the sender$'
    )
)
def _sends_without_sender(world, who, text):
    """The update reaches the bot without the author (e.g. the message was deleted meanwhile)."""
    world.send(who, text, with_sender=False)


@when(parsers.re(r'"(?P<who>[^"]+)" edits a message into "(?P<text>[^"]*)"$'))
def _edits(world, who, text):
    """The user edits one of their messages so that it now reads `text`."""
    world.send(who, text, edited=True)


@when(parsers.re(r'"(?P<who>[^"]+)" sends the message:$'))
def _sends_multiline(world, who, docstring):
    """Like `sends "<text>"`, for texts spanning several lines."""
    world.send(who, interpolate(world, docstring))


@when("the scheduled jobs run")
def _jobs_run(world):
    world.run_scheduled_jobs()


# ---- Then: bot output ------------------------------------------------------------------------------


def _next_call_as(world, method):
    call = world.next_call()
    assert call.method == method, f"Expected the bot to {method}, but it did: {call}"
    # jobs address the chat with its id as a string (see reminder_steps.py): compare the id, not the type
    assert int(call.params["chat_id"]) == world.current_chat.id, (
        f"Wrong chat: expected {world.current_chat.id}, got {call.params['chat_id']}"
    )
    return call


def _assert_message(call, text, parse_mode, keys):
    assert set(call.params) == keys, f"Unexpected parameters: {sorted(call.params)}"
    assert call.params.get("parse_mode") == parse_mode, "Unexpected parse mode"
    assert call.params["text"] == text, (
        "the bot's text (+) differs from the scenario's text (-)"
    )


@then("the bot should send:")
def _bot_sends(world, docstring):
    """Next outgoing message: Markdown text, exactly this."""
    _send_markdown(world, interpolate(world, docstring))


@then(parsers.parse('the bot should send the text "{name}"'))
def _bot_sends_named(world, name):
    """Same as `the bot should send:` with a text defined by `the text "<name>" is:`."""
    _send_markdown(world, interpolate(world, "{" + name + "}"))


def _send_markdown(world, text):
    call = _next_call_as(world, "send_message")
    _assert_message(call, text, "markdown", {"chat_id", "parse_mode", "text"})


@then("the bot should send plain text:")
def _bot_sends_plain(world, docstring):
    call = _next_call_as(world, "send_message")
    _assert_message(call, interpolate(world, docstring), None, {"chat_id", "text"})


@then(parsers.parse('the bot should send the plain text "{name}"'))
def _bot_sends_plain_named(world, name):
    """Same as `the bot should send plain text:` with a text defined by `the text "<name>" is:`."""
    call = _next_call_as(world, "send_message")
    _assert_message(
        call, interpolate(world, "{" + name + "}"), None, {"chat_id", "text"}
    )


@then(parsers.re(r'the bot should send the quoted text "(?P<text>[^"]*)"$'))
def _bot_sends_quoted(world, text):
    """Like `the bot should send:` for one-line texts whose leading/trailing spaces a docstring would lose."""
    _send_markdown(world, text)


@then("the bot should edit the summary to:")
def _bot_edits_summary(world, docstring):
    """Edit of the message the bot keeps as the match summary (the one tracked for the chat)."""
    call = _next_call_as(world, "edit_message_text")
    match = world.db.fetch_match(world.current_chat.id)
    assert match is not None, "There is no match, so there is no summary to edit."
    assert call.params["message_id"] == match["summary_message_id"], (
        f"Edited message {call.params['message_id']}, "
        f"but the summary is message {match['summary_message_id']}"
    )
    _assert_message(
        call,
        interpolate(world, docstring),
        "markdown",
        {"chat_id", "message_id", "parse_mode", "text"},
    )


@then("the bot should pin the last message")
def _bot_pins_last(world):
    """Pins the message of the most recent `send_message` already asserted by the scenario."""
    sent_so_far = sum(
        c.method == "send_message" for c in world.telegram.calls[: world.consumed]
    )
    assert sent_so_far, (
        "The scenario asserted no message sent by the bot before the pin."
    )
    expected = world.telegram.sent_ids[sent_so_far - 1]
    call = _next_call_as(world, "pin_chat_message")
    assert set(call.params) == {"chat_id", "message_id"}
    assert call.params["message_id"] == expected, (
        f"Pinned message {call.params['message_id']}, "
        f"but the message just sent is {expected}"
    )


@then("the bot should pin the summary")
def _bot_pins_summary(world):
    """Pins the message the bot tracks as the match summary (after an edit it is not the bot's last one)."""
    call = _next_call_as(world, "pin_chat_message")
    summary_id = _match_of_this_chat(world)["summary_message_id"]
    assert set(call.params) == {"chat_id", "message_id"}
    assert call.params["message_id"] == summary_id, (
        f"Pinned message {call.params['message_id']}, but the summary is message {summary_id}"
    )


@then(parsers.parse('the bot should fail with "{exception_type}"'))
def _bot_failed(world, exception_type):
    """Consumes the oldest recorded handler exception, which must be of this type."""
    assert world.errors, "Expected the bot to crash, but no exception was raised."
    actual = type(world.errors[0]).__name__
    assert actual == exception_type, (
        f"Expected {exception_type}, the bot raised {actual}"
    )
    world.errors.pop(0)


def logged_warnings(caplog):
    """Every warning (or worse) logged during the scenario, in order, as (level, message)."""
    return [
        (record.levelname, record.getMessage())
        for record in caplog.records
        if record.levelno >= logging.WARNING
    ]


@then(parsers.parse('the bot should log the warning "{text}"'))
def _bot_logs_warning(world, caplog, text):
    """Consumes the oldest logged warning, which must be exactly this one."""
    pending = logged_warnings(caplog)[world.consumed_warnings :]
    assert pending, f'Expected the bot to log "{text}", but it logged nothing more.'
    assert pending[0] == ("WARNING", text)
    world.consumed_warnings += 1


@then("the bot should send nothing else")
def _bot_nothing_else(world):
    extra = world.unconsumed()
    assert not extra, "The bot did more than expected:\n" + "\n".join(map(str, extra))


# ---- Then: persisted match ---------------------------------------------------------------------------


def _render(field, match):
    value = match[field if field != "summary message" else "summary_message_id"]
    if value is None:
        return NONE
    if field == "players":
        return ", ".join(
            f"{name} (maybe)" if is_maybe else name for name, is_maybe in value
        )
    if field == "teams":
        return " | ".join(
            f"{name}: {', '.join(people)}" for name, people in value.items()
        )
    return str(value)


FIELDS = {
    "players": "players",
    "target": "target",
    "day": "day",
    "time": "time",
    "pitch": "pitch",
    "description": "description",
    "teams": "teams",
    "summary message": "summary message",
}


def _match_of_this_chat(world):
    match = world.db.fetch_match(world.current_chat.id)
    assert match is not None, "There is no match for this chat."
    return match


@then("the match should have:")
def _match_has(world, datatable):
    """Exact value of each listed field of this chat's match; `(none)` stands for empty."""
    rows = [row for row in datatable if row != HEADER]
    unknown = [r[0] for r in rows if r[0] not in FIELDS]
    assert not unknown, f"Unknown match field(s): {unknown}; known: {sorted(FIELDS)}"
    match = _match_of_this_chat(world)
    expected = [(r[0], r[1].replace("\\n", "\n")) for r in rows]
    actual = [(field, _render(FIELDS[field], match)) for field, _ in expected]
    wrong = [
        f"{field}: expected {want!r}, got {got!r}"
        for (field, want), (_, got) in zip(expected, actual)
        if want != got
    ]
    assert not wrong, "Match differs:\n" + "\n".join(wrong)


@then(parsers.re(r"the match (?P<field>description|pitch) should be:$"))
def _match_text_field(world, field, docstring):
    assert _render(field, _match_of_this_chat(world)) == interpolate(world, docstring)


@then("there should be no match for this chat")
def _no_match(world):
    assert world.db.fetch_match(world.current_chat.id) is None, (
        "A match exists for this chat."
    )


@then(parsers.parse('there should be a match for "{title}"'))
def _match_exists_for(world, title):
    assert world.db.fetch_match(world.chats[title].id) is not None, (
        f"There is no match for chat {title!r}."
    )


@then(parsers.parse('the match of "{title}" should have no players'))
def _other_match_has_no_players(world, title):
    match = world.db.fetch_match(world.chats[title].id)
    assert match is not None, f"There is no match for chat {title!r}."
    assert match["players"] is None, f"Unexpected players: {match['players']}"


# ---- Then: how the job addresses the chat -------------------------------------------------------------
# The job sends with `chat_id = job.name`, i.e. the chat id as a STRING, while handlers use the integer id.
# Telegram accepts both, so the generic steps compare the id regardless of its type; this step documents
# the actual type used by the job.


@then("the last thing the bot did should address the chat with its id as a string")
def _addressed_with_string_id(world):
    call = world.telegram.calls[world.consumed - 1]
    assert isinstance(call.params["chat_id"], str), (
        f"Expected a string chat_id, got {call.params['chat_id']!r}"
    )
    assert call.params["chat_id"] == str(world.current_chat.id)


@then("the match summary message should be the last message of the bot")
def _summary_is_last(world):
    match = world.db.fetch_match(world.current_chat.id)
    assert match["summary_message_id"] == world.last_bot_message_id()
