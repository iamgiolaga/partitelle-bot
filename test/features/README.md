# Feature tests

Behaviour-level scenarios (Gherkin, pytest-bdd) run against the REAL handlers, python-telegram-bot `Application`, job queue and a REAL Postgres. Only the Telegram network edge and the clock are faked.

## Run locally

```sh
docker compose up -d --wait          # Postgres 17 on localhost:5432 (user/password: partitelle)
uv run pytest                        # whole suite, uses database partitelle_test
PB_DB_NAME=partitelle_integration_test uv run pytest   # another database (the name MUST end with _test: its schema is dropped and rebuilt)
uv run pytest test/features -k "teams"                 # a subset
```

Any `PB_*` variable can be overridden from the environment (defaults: `test/conftest.py`).

## How the harness works

- `pg_harness.py`: the only place that knows the DB schema (`Database` helpers take and return plain test values); creates the test database if missing, rebuilds the schema with the real migrations (`db/migrate.py`), truncates it before every scenario.
- `telegram_world.py`: `FakeTelegram` (a `telegram.request.BaseRequest`) records every outgoing Bot API call (send, edit, pin, ...) and answers with plausible JSON; an unsupported call fails the scenario. Handlers are registered through the real `register_handlers` on a real `Application`.
- The steps are synchronous: every coroutine runs on a dedicated event loop owned by the `World` (one per scenario). `World.send` feeds a message with `application.process_update`; `World.run_scheduled_jobs` awaits the jobs captured by the (never started) job queue. `test_python_only_paths.py` holds plain pytest tests for the few paths no scenario describes.
- Every call is recorded in order and each `Then the bot should ...` step consumes the next one. After each scenario (`conftest.py`) any unconsumed bot call, any recorded handler exception or any logged warning (or error) that was not asserted fails the scenario.
- Given steps that replay messages (`had sent`, `a match was started`) or write the DB directly are setup: their bot traffic is forgotten and is not part of the expectations.

## Writing scenarios

- Describe behaviour only (what users send, what the bot answers, what is persisted), never PTB/DB internals.
- Strict: full-text equality of every message, exact parameters (parse mode, chat, message id); no "contains".
- Every bot action must be asserted, in order, and closed with `And the bot should send nothing else` where nothing more is expected.
- Long texts live in `Given the text "<name>" is:` (docstring, usable in a `Background:`); reference them as `{name}` inside docstrings (exact string substitution, a placeholder may use earlier ones) or with `Then the bot should send the text "<name>"`.
- Deterministic: freeze time with `today is`, seed the draw, use deterministic ordering.
- Known bugs: tag the scenario `@known-bug` (+ `@issue-NN` when a GitHub issue exists) and assert the CURRENT behaviour, so fixing the bug breaks the scenario and forces an update. Every tag must be registered in `[tool.pytest.ini_options] markers` (pyproject.toml).
- Prefer extending an existing scenario file; reuse existing phrases, add a new step only if no phrase fits (`feature_steps/steps.py`, reminder-only steps in `reminder_steps.py`).

## Step phrases

### Given
- `the text "<name>" is:` + docstring: defines a named text for `{name}` / `the text "<name>"`.
- `a group chat "<title>"`: creates a chat and makes it the current one.
- `the user "@<username>"`: a user with that username.
- `a user named "<name>" without username`: a user with no username (first name only).
- `a user named "<first>" "<last>" without username`: a user with no username, first and last name (label: `<first> <last>`).
- `the current chat is "<title>"`: switches the chat later steps refer to (also usable as Then).
- `a match was started`: really sends `/start` (creates an organizer user if none exists); traffic forgotten.
- `"<user>" had sent "<text>"` / `... in "<chat>"`: really sends the message as setup; traffic forgotten.
- `the match target is <n>`: sets the target directly in the DB.
- `the chat has the default pitch "<pitch>"`: gives the chat a setting row with that default pitch, as if it had been set up before.
- `the match has the players "<a, b (maybe), ...>"`: sets the list directly, in order; ` (maybe)` marks a maybe-present player (how participants are stored lives only in `pg_harness.py`).
- `the match has the black team "<...>" and the white team "<...>"`: sets the teams directly.
- `the bot is not an administrator of the chat`: pinning fails with "not enough rights".
- `today is "<YYYY-MM-DD HH:MM>"`: freezes the clock (Europe/Rome).
- `the clock moves to "<YYYY-MM-DD HH:MM>"`: re-freezes the clock at another moment.
- `the team draw is seeded with <n>`: seeds the random team draw.
- `the bot is expected to crash on the next message`: handler exceptions are recorded instead of re-raised (see below).

### When
- `"<user>" sends "<text>"` / `... in "<chat>"`: sends a one-line message (to the current or the given chat).
- `"<user>" sends the message:` + docstring: same, for multi-line text.
- `"<user>" edits a message into "<text>"`: the user edits one of their messages, which now reads `<text>` (an `edited_message` update).
- `the scheduled jobs run`: runs every job captured by the job queue (payment reminders).

### Then
- `the bot should send:` + docstring: next call is a Markdown `send_message` with exactly this text.
- `the bot should send the text "<name>"`: same, with a named text.
- `the bot should send the quoted text "<text>"`: same, one line, keeps leading/trailing spaces.
- `the bot should send plain text:` / `the bot should send the plain text "<name>"`: next call is a `send_message` without parse mode.
- `the bot should edit the summary to:` + docstring: next call edits the tracked summary message with exactly this Markdown text.
- `the bot should pin the last message`: next call pins the last message the scenario asserted as sent.
- `the bot should pin the summary`: next call pins the tracked summary message.
- `the bot should send nothing else`: no unconsumed bot calls remain.
- `the bot should fail with "<ExceptionType>"`: consumes the oldest recorded handler exception, which must be of this type.
- `the bot should log the warning "<text>"`: consumes the oldest logged warning (or error), which must be a warning with exactly this message.
- `the match should have:` + `| field | value |` table: exact persisted values (fields: players, target, day, time, pitch, description, teams, summary message; `(none)` = empty).
- `the match description should be:` / `the match pitch should be:` + docstring: exact text.
- `the match summary message should be the last message of the bot`: tracked summary id equals the bot's last sent message.
- `there should be no match for this chat` / `there should be a match for "<chat>"`: existence of the match.
- `the match of "<chat>" should have no players`: other chat's match is empty.
- `a payment reminder should be scheduled for "<YYYY-MM-DD HH:MM>"` / `<n> payment reminders should be scheduled for "<...>"` / `no payment reminder should be scheduled`: reminders queued for the current chat (Europe/Rome).
- `the last thing the bot did should address the chat with its id as a string`: documents that jobs use a string chat id.

## Determinism hooks

`today is` / `the clock moves to` freeze the clock (time-machine) and the timezone to Europe/Rome, restored after each scenario; `the team draw is seeded with` seeds `random` and restores its state.

## Crash expectations

When the bot is known to crash (unhandled handler exception), the scenario declares it with `Given the bot is expected to crash on the next message`, then asserts each exception with `Then the bot should fail with "<ExceptionType>"`. Without the Given a crash fails the scenario immediately; with it, an exception that is not asserted fails the scenario at the end. Crashes are tagged `@known-bug`.
