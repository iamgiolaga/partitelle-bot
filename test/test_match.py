import unittest
from datetime import datetime

import time_machine

from domain import Match, Participant, TargetTooLow, Teams
from domain.schedule import TIMEZONE


def _at(*moment):
    return datetime(*moment, tzinfo=TIMEZONE)


def _match(*participants, target=4):
    return Match(chat_id=1, participants=list(participants), target=target)


class TestMatch(unittest.TestCase):
    def test_find_distinguishes_confirmed_from_maybe(self):
        match = _match(Participant("anna"), Participant("bea", True))
        self.assertEqual(match.find("anna", False), Participant("anna"))
        self.assertIsNone(match.find("anna", True))
        self.assertEqual(match.find("bea", True), Participant("bea", True))
        self.assertIsNone(match.find("bea", False))
        self.assertIsNone(match.find("carlo", False))

    def test_find_ignores_the_case_of_the_name(self):
        match = _match(Participant("Anna"), Participant("bea", True))
        self.assertEqual(match.find("anna", False), Participant("Anna"))
        self.assertEqual(match.find("BEA", True), Participant("bea", True))
        self.assertIsNone(match.find("anna", True))

    def test_counts(self):
        empty = _match()
        self.assertEqual((empty.confirmed_count, empty.maybe_count), (0, 0))
        self.assertEqual(empty.confirmed_names(), [])
        match = _match(Participant("a"), Participant("b", True), Participant("c"))
        self.assertEqual(match.confirmed_names(), ["a", "c"])
        self.assertEqual((match.confirmed_count, match.maybe_count), (2, 1))

    def test_has_room_counts_maybes(self):
        self.assertTrue(_match(Participant("a"), target=2).has_room)
        full = _match(Participant("a"), Participant("b", True), target=2)
        self.assertFalse(full.has_room)

    def test_check_new_target_refuses_below_the_people_in_the_list(self):
        match = _match(*(Participant(name) for name in "abcd"), target=10)
        self.assertEqual(match.check_new_target(3), TargetTooLow(3, 4, 0))
        self.assertEqual(TargetTooLow(3, 4, 0).total, 4)

    def test_check_new_target_counts_maybes(self):
        match = _match(
            Participant("a"),
            Participant("b"),
            Participant("c", True),
            Participant("d", True),
        )
        refusal = match.check_new_target(3)
        self.assertEqual(refusal, TargetTooLow(requested=3, confirmed=2, maybe=2))
        self.assertEqual(refusal.total if refusal else None, 4)
        only_maybes = _match(Participant("a", True), Participant("b", True), target=10)
        self.assertEqual(only_maybes.check_new_target(1), TargetTooLow(1, 0, 2))

    def test_check_new_target_accepts_the_list_size_or_more(self):
        match = _match(Participant("a"), Participant("b", True), target=10)
        self.assertIsNone(match.check_new_target(2))
        self.assertIsNone(match.check_new_target(3))
        self.assertIsNone(_match().check_new_target(2))

    def test_new_holds_the_defaults(self):
        with time_machine.travel(_at(2026, 10, 21, 21, 0), tick=False):
            match = Match.new("42")
        self.assertEqual(match.chat_id, 42)
        self.assertEqual(match.participants, [])
        self.assertEqual(match.target, 10)
        self.assertIn("MAGLIA BIANCA", match.description)
        self.assertEqual(match.starts, _at(2026, 10, 28, 20, 0))
        self.assertIsNone(match.pitch)
        self.assertIsNone(match.summary_message_id)
        self.assertIsNone(match.teams)
        self.assertEqual(Match.new(1, "campo").pitch, "campo")

    def test_new_matches_do_not_share_participants(self):
        first, second = Match.new(1), Match.new(2)
        first.participants.append(Participant("a"))
        self.assertEqual(second.participants, [])


class TestTeams(unittest.TestCase):
    def test_members_contains_and_as_dict(self):
        teams = Teams(("a", "b"), ("c",))
        self.assertEqual(teams.members, ("a", "b", "c"))
        self.assertTrue(teams.contains("c"))
        self.assertFalse(teams.contains("d"))
        self.assertTrue(teams.contains("C"))
        self.assertEqual(teams.colour_of("A"), "black")
        self.assertEqual(teams.colour_of("c"), "white")
        self.assertIsNone(teams.colour_of("d"))
        self.assertEqual(teams.as_dict(), {"black": ["a", "b"], "white": ["c"]})
        self.assertEqual(list(teams.as_dict()), ["black", "white"])


if __name__ == "__main__":
    unittest.main()
