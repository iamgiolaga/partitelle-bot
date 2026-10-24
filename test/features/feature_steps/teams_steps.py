"""Step definitions used by teams.feature (setup shortcuts replaying real messages)."""

from pytest_bdd import given, parsers


@given(parsers.parse('"{who}" added the players "{names}"'))
def _players_added(world, who, names):
    """Replays real `aggiungi <name>` messages; their traffic is setup, not part of the expectations."""
    for name in names.split(", "):
        world.send(who, f"aggiungi {name}")
    world.forget_calls()


@given(parsers.parse('"{who}" set the target to {target:d}'))
def _target_set(world, who, target):
    world.send(who, f"/setnumber {target}")
    world.forget_calls()


@given(parsers.parse('"{who}" asked for the teams'))
def _teams_asked(world, who):
    world.send(who, "/teams")
    world.forget_calls()
