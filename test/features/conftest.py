# ruff: noqa: E402
import os
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
import time_machine

pytest.register_assert_rewrite(
    "feature_steps.steps"
)  # readable diffs from step asserts

from pg_harness import Database, prepare_database
from telegram_world import World
from feature_steps.steps import *  # noqa: F401,F403  (registers the step definitions)
from feature_steps.steps import logged_warnings
from feature_steps.reminder_steps import *  # noqa: F401,F403


@pytest.fixture(scope="session", autouse=True)
def _database_schema():
    prepare_database()


@pytest.fixture
def db(_database_schema):
    database = Database()
    database.truncate()
    yield database
    database.close()


@pytest.fixture
def world(db):
    world = World()
    world.db = db
    yield world
    world.close()
    if world.clock is not None:
        world.clock.stop()
        world.clock = None
    os.environ.pop("TZ", None)
    time.tzset()


@pytest.fixture
def freeze_time(world):
    """Callable used by the `today is ...` step: freezes the clock in Europe/Rome."""

    def _freeze(text):
        os.environ["TZ"] = "Europe/Rome"
        time.tzset()
        moment = datetime.strptime(text, "%Y-%m-%d %H:%M").replace(
            tzinfo=ZoneInfo("Europe/Rome")
        )
        world.clock = time_machine.travel(moment, tick=False)
        world.clock.start()

    return _freeze


def pytest_bdd_after_scenario(request, feature, scenario):
    """Strictness: every outgoing bot call must have been asserted by the scenario."""
    if (
        sys.exc_info()[0] is not None
    ):  # the scenario already failed, do not mask the real error
        return
    world = request.getfixturevalue("world")
    if world.errors:
        raise AssertionError(f"Unasserted bot crash(es): {world.errors}")
    warnings = logged_warnings(request.getfixturevalue("caplog"))
    if warnings[world.consumed_warnings :]:
        raise AssertionError(
            f"Unasserted logged warning(s): {warnings[world.consumed_warnings :]}"
        )
    extra = world.unconsumed()
    if extra:
        lines = "\n".join(f"  - {call}" for call in extra)
        raise AssertionError(
            f"The bot did {len(extra)} unexpected thing(s) not covered by the scenario:\n{lines}"
        )
