import unittest

from db.repository import _encode_participant, _row_to_match
from domain import Match, Participant, Teams


class TestRowToMatch(unittest.TestCase):
    def test_decodes_a_full_row(self):
        row = (
            ["@anna", "bea%is%maybe%present"],
            "Mercoledì 28/10/2026",
            "20:00",
            10,
            "msg\n",
            "campo",
            {"black": ["a"], "white": ["b"]},
            77,
        )
        self.assertEqual(
            _row_to_match("5", row),
            Match(
                5,
                [Participant("@anna"), Participant("bea", True)],
                "Mercoledì 28/10/2026",
                "20:00",
                10,
                "msg\n",
                "campo",
                77,
                Teams(("a",), ("b",)),
            ),
        )

    def test_null_columns_decode_to_empty_values(self):
        match = _row_to_match(5, (None, "d", "20:00", 10, None, None, None, None))
        self.assertEqual(match.participants, [])
        self.assertIsNone(match.teams)
        self.assertIsNone(match.pitch)
        self.assertIsNone(match.summary_message_id)

    def test_only_a_trailing_suffix_marks_a_maybe(self):
        players = ["a", "b%is%maybe%present"]
        match = _row_to_match(1, (players, "d", "t", 2, "", None, None, None))
        self.assertEqual([p.is_maybe for p in match.participants], [False, True])
        self.assertEqual([p.name for p in match.participants], ["a", "b"])

    def test_encoding_round_trips_the_maybe_suffix(self):
        for participant in [Participant("@anna"), Participant("bea", True)]:
            row = (
                [_encode_participant(participant)],
                "d",
                "t",
                2,
                "",
                None,
                None,
                None,
            )
            self.assertEqual(_row_to_match(1, row).participants, [participant])


if __name__ == "__main__":
    unittest.main()
