"""Step definitions. Wording is behaviour-level; everything PTB/DB specific lives behind `world`."""

import re

from pytest_bdd import given, parsers, then, when

HEADER = ["field", "value"]
NONE = "(none)"
MAYBE_MARKER = "%is%maybe%present"  # how a "maybe" player is persisted

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


@given(parsers.parse('a user named "{name}" without username'))
def _user_without_username(world, name):
    world.add_user(name, name, None)


@given(parsers.parse('today is "{when}"'))
def _today(freeze_time, when):
    """Freezes the clock at `when` (YYYY-MM-DD HH:MM, Europe/Rome)."""
    freeze_time(when)


@given("a match was started")
def _match_was_started(world):
    if not world.users:
        world.add_user("@organizer", "Organizer", "organizer")
    world.send(next(iter(world.users)), "/start")
    world.forget_calls()


@given("the bot is not an administrator of the chat")
def _bot_not_admin(world):
    world.bot.can_pin = False


# ---- When ------------------------------------------------------------------------------------------


@when(parsers.re(r'"(?P<who>[^"]+)" sends "(?P<text>[^"]*)"$'))
def _sends(world, who, text):
    world.send(who, text)


@when(parsers.re(r'"(?P<who>[^"]+)" sends "(?P<text>[^"]*)" in "(?P<title>[^"]+)"$'))
def _sends_in(world, who, text, title):
    world.send(who, text, chat=world.chats[title])


@when("the scheduled jobs run")
def _jobs_run(world):
    world.run_scheduled_jobs()


# ---- Then: bot output ------------------------------------------------------------------------------


def _next_call_as(world, method):
    call = world.next_call()
    assert call.method == method, f"Expected the bot to {method}, but it did: {call}"
    assert (
        call.params["chat_id"] == world.current_chat.id
    ), f"Wrong chat: expected {world.current_chat.id}, got {call.params['chat_id']}"
    return call


def _assert_message(call, text, parse_mode, keys):
    assert set(call.params) == keys, f"Unexpected parameters: {sorted(call.params)}"
    assert call.params.get("parse_mode") == parse_mode, "Unexpected parse mode"
    assert (
        call.params["text"] == text
    ), "the bot's text (+) differs from the scenario's text (-)"


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
    call = _next_call_as(world, "pin_chat_message")
    assert set(call.params) == {"chat_id", "message_id"}
    assert call.params["message_id"] == world.last_bot_message_id(), (
        f"Pinned message {call.params['message_id']}, "
        f"but the bot's last message is {world.last_bot_message_id()}"
    )


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
            p[: -len(MAYBE_MARKER)] + " (maybe)" if p.endswith(MAYBE_MARKER) else p
            for p in value
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
    assert (
        world.db.fetch_match(world.current_chat.id) is None
    ), "A match exists for this chat."


@then(parsers.parse('there should be a match for "{title}"'))
def _match_exists_for(world, title):
    assert (
        world.db.fetch_match(world.chats[title].id) is not None
    ), f"There is no match for chat {title!r}."
