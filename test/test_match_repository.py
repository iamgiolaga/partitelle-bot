import unittest

from db.repository import _teams_from, _team_of, _validate_new_participant
from domain import Participant, Teams


class TestTeamsFrom(unittest.TestCase):
    def test_no_team_at_all_means_no_teams(self):
        self.assertIsNone(_teams_from([("anna", "confirmed", None)]))
        self.assertIsNone(_teams_from([]))

    def test_members_keep_the_order_of_the_rows(self):
        rows = [
            ("a", "confirmed", "white"),
            ("b", "confirmed", "black"),
            ("c", "maybe", None),
            ("d", "confirmed", "white"),
            ("e", "confirmed", "black"),
        ]
        self.assertEqual(_teams_from(rows), Teams(("b", "e"), ("a", "d")))


class TestTeamOf(unittest.TestCase):
    def test_names_are_lowercased_and_nothing_means_no_colour(self):
        self.assertEqual(
            _team_of(Teams(("Anna",), ("bea",))), {"anna": "black", "bea": "white"}
        )
        self.assertEqual(_team_of(None), {})


class TestValidateNewParticipant(unittest.TestCase):
    def test_empty_and_command_names_are_refused(self):
        for participant in [
            Participant(""),
            Participant("  "),
            Participant("", True),
            Participant("/start"),
            Participant("/stop", True),
        ]:
            with self.assertRaises(ValueError):
                _validate_new_participant(participant)

    def test_ordinary_names_are_accepted(self):
        _validate_new_participant(Participant("anna"))
        _validate_new_participant(Participant("anna", True))


if __name__ == "__main__":
    unittest.main()
