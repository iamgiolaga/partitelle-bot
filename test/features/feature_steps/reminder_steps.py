"""Steps for the payment reminder feature (scheduled job asserted at behaviour level)."""

from zoneinfo import ZoneInfo

from pytest_bdd import parsers, then

ROME = ZoneInfo("Europe/Rome")


# ---- helpers ----------------------------------------------------------------------------------------


def _reminders_of_this_chat(world):
    """Fire times (Europe/Rome, 'YYYY-MM-DD HH:MM') of the reminders scheduled for the current chat."""
    name = str(world.current_chat.id)
    return sorted(
        job.job.trigger.run_date.astimezone(ROME).strftime("%Y-%m-%d %H:%M")
        for job in world.job_queue.jobs()
        if job.name == name
    )


# ---- Then: scheduled reminders ----------------------------------------------------------------------


@then(parsers.parse('a payment reminder should be scheduled for "{when}"'))
def _one_reminder(world, when):
    assert _reminders_of_this_chat(world) == [when], (
        f"Expected exactly one reminder at {when}, "
        f"got {_reminders_of_this_chat(world)}"
    )


@then(
    parsers.re(
        r'(?P<count>\d+) payment reminders should be scheduled for "(?P<when>[^"]+)"$'
    )
)
def _many_reminders(world, count, when):
    assert _reminders_of_this_chat(world) == [when] * int(
        count
    ), f"Expected {count} reminders at {when}, got {_reminders_of_this_chat(world)}"


@then("no payment reminder should be scheduled")
def _no_reminder(world):
    assert (
        _reminders_of_this_chat(world) == []
    ), f"Unexpected reminder(s): {_reminders_of_this_chat(world)}"
