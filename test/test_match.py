import unittest

from domain import Match, Participant, Teams


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

    def test_new_holds_the_defaults(self):
        match = Match.new("42", "Mercoledì 28/10/2026")
        self.assertEqual(match.chat_id, 42)
        self.assertEqual(match.participants, [])
        self.assertEqual((match.time, match.target), ("20:00", 10))
        self.assertIn("MAGLIA BIANCA", match.description)
        self.assertEqual(match.day, "Mercoledì 28/10/2026")
        self.assertIsNone(match.pitch)
        self.assertIsNone(match.summary_message_id)
        self.assertIsNone(match.teams)
        self.assertEqual(Match.new(1, "d", "campo").pitch, "campo")

    def test_new_matches_do_not_share_participants(self):
        first, second = Match.new(1, "d"), Match.new(2, "d")
        first.participants.append(Participant("a"))
        self.assertEqual(second.participants, [])


class TestTeams(unittest.TestCase):
    def test_members_contains_and_as_dict(self):
        teams = Teams(("a", "b"), ("c",))
        self.assertEqual(teams.members, ("a", "b", "c"))
        self.assertTrue(teams.contains("c"))
        self.assertFalse(teams.contains("d"))
        self.assertEqual(teams.as_dict(), {"black": ["a", "b"], "white": ["c"]})
        self.assertEqual(list(teams.as_dict()), ["black", "white"])


if __name__ == "__main__":
    unittest.main()
