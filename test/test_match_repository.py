import unittest
from datetime import date, datetime

from db.repository import (
    _decode_starts,
    _encode_participant,
    _row_to_match,
    _validate_new_participant,
)
from domain import Match, Participant, Teams
from domain.schedule import TIMEZONE


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
                datetime(2026, 10, 28, 20, 0, tzinfo=TIMEZONE),
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


class TestDecodeStarts(unittest.TestCase):
    # a Thursday: the next Wednesday is the 28th
    today = date(2026, 10, 22)

    def _decode(self, day, at):
        return _decode_starts(day, at, self.today)

    def test_a_date_with_or_without_the_weekday(self):
        expected = datetime(2026, 10, 25, 21, 30, tzinfo=TIMEZONE)
        for day in ["25/10/2026", "Domenica 25/10/2026", "domenica 25.10.2026"]:
            self.assertEqual(self._decode(day, "21:30"), expected)

    def test_a_weekday_alone_is_the_next_such_weekday(self):
        self.assertEqual(
            self._decode("Sabato", "20:00"),
            datetime(2026, 10, 24, 20, 0, tzinfo=TIMEZONE),
        )
        self.assertEqual(
            self._decode("giovedi", "20:00"),
            datetime(2026, 10, 29, 20, 0, tzinfo=TIMEZONE),
        )

    def test_a_bare_hour_and_other_time_spellings(self):
        for at, expected in [("20", (20, 0)), ("9.05", (9, 5)), (" 7:30 ", (7, 30))]:
            self.assertEqual(
                self._decode("25/10/2026", at),
                datetime(2026, 10, 25, *expected, tzinfo=TIMEZONE),
            )

    def test_anything_unreadable_falls_back_to_the_next_wednesday_at_eight(self):
        fallback = datetime(2026, 10, 28, 20, 0, tzinfo=TIMEZONE)
        for day, at in [("boh", "sera"), (None, None), ("", ""), ("31/02/2026", "25")]:
            self.assertEqual(self._decode(day, at), fallback)

    def test_a_readable_day_keeps_the_default_time_when_the_time_is_not(self):
        self.assertEqual(
            self._decode("25/10/2026", "sera"),
            datetime(2026, 10, 25, 20, 0, tzinfo=TIMEZONE),
        )


class TestEncodeParticipant(unittest.TestCase):
    def test_a_maybe_gets_the_suffix(self):
        self.assertEqual(_encode_participant(Participant("anna")), "anna")
        self.assertEqual(
            _encode_participant(Participant("anna", True)), "anna%is%maybe%present"
        )


class TestValidateNewParticipant(unittest.TestCase):
    def test_empty_and_command_names_are_refused(self):
        for participant in [
            Participant(""),
            Participant("  "),
            Participant("", True),
            Participant("%is%maybe%present"),
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
