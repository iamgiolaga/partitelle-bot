import unittest
from datetime import date, datetime, time

from domain.schedule import (
    TIMEZONE,
    format_day,
    format_time,
    next_start,
    next_weekday,
    parse_day,
    parse_time,
    with_day,
    with_time,
)


def _at(*moment):
    return datetime(*moment, tzinfo=TIMEZONE)


class TestNextStart(unittest.TestCase):
    def test_every_day_of_the_week(self):
        # 2021-11-08 is a Monday
        for day, expected in [
            (8, 10),
            (9, 10),
            (10, 10),
            (11, 17),
            (12, 17),
            (13, 17),
            (14, 17),
        ]:
            self.assertEqual(
                next_start(_at(2021, 11, day, 12, 0)), _at(2021, 11, expected, 20, 0)
            )

    def test_on_wednesday_it_depends_on_the_match_time(self):
        for hour, minute, expected in [
            (8, 0, 10),
            (19, 59, 10),
            (20, 0, 17),
            (20, 1, 17),
            (23, 59, 17),
        ]:
            self.assertEqual(
                next_start(_at(2021, 11, 10, hour, minute)),
                _at(2021, 11, expected, 20, 0),
            )

    def test_the_clock_of_another_zone_is_read_in_rome(self):
        utc_evening = datetime.fromisoformat("2021-11-10T19:30:00+00:00")  # 20:30 Rome
        self.assertEqual(next_start(utc_evening), _at(2021, 11, 17, 20, 0))

    def test_without_arguments_it_uses_the_clock(self):
        self.assertGreater(next_start(), datetime.now(TIMEZONE))

    def test_next_weekday_is_strictly_after_today(self):
        self.assertEqual(next_weekday(date(2021, 11, 10), 2), date(2021, 11, 17))
        self.assertEqual(next_weekday(date(2021, 11, 12), 4), date(2021, 11, 19))
        self.assertEqual(next_weekday(date(2021, 11, 7), 0), date(2021, 11, 8))


class TestFormat(unittest.TestCase):
    def test_the_canonical_day_and_time(self):
        starts = _at(2026, 11, 4, 9, 5)
        self.assertEqual(format_day(starts), "Mercoledì 04/11/2026")
        self.assertEqual(format_time(starts), "09:05")

    def test_every_weekday_has_its_italian_name(self):
        names = [format_day(_at(2026, 11, day)).split()[0] for day in range(2, 9)]
        self.assertEqual(
            names,
            [
                "Lunedì",
                "Martedì",
                "Mercoledì",
                "Giovedì",
                "Venerdì",
                "Sabato",
                "Domenica",
            ],
        )


class TestParseDay(unittest.TestCase):
    def test_dates_with_an_optional_italian_weekday(self):
        for text in [
            "Mercoledì 28/10/2026",
            "mercoledi 28/10/2026",
            "MERCOLEDÌ 28/10/2026",
            "28/10/2026",
            "28.10.2026",
            "28-10-2026",
        ]:
            self.assertEqual(parse_day(text), date(2026, 10, 28), text)

    def test_the_day_comes_first(self):
        self.assertEqual(parse_day("03/11/2026"), date(2026, 11, 3))

    def test_a_trailing_time_is_ignored(self):
        self.assertEqual(parse_day("Mercoledì 28/10/2026 21:30"), date(2026, 10, 28))

    def test_unreadable_text_is_none(self):
        for text in ["Mercoledì", "prossima settimana", "boh", "31/02/2026", "9" * 40]:
            self.assertIsNone(parse_day(text), text)


class TestParseTime(unittest.TestCase):
    def test_accepted_spellings(self):
        for text, expected in [
            ("21:30", time(21, 30)),
            ("9:30", time(9, 30)),
            ("0:00", time(0, 0)),
            ("23:59", time(23, 59)),
            ("21.30", time(21, 30)),
            ("9.05", time(9, 5)),
            (" 21:30 ", time(21, 30)),
            ("20", time(20, 0)),
            ("0", time(0, 0)),
            ("9", time(9, 0)),
        ]:
            self.assertEqual(parse_time(text), expected, text)

    def test_rejected_text(self):
        for text in ["25:99", "24:00", "24", "21:60", "stasera", "alle 21", "21:5", ""]:
            self.assertIsNone(parse_time(text), text)


class TestReplaceOnePart(unittest.TestCase):
    def test_with_day_keeps_the_time(self):
        self.assertEqual(
            with_day(_at(2026, 10, 28, 21, 30), date(2026, 11, 4)),
            _at(2026, 11, 4, 21, 30),
        )

    def test_with_time_keeps_the_day(self):
        self.assertEqual(
            with_time(_at(2026, 10, 28, 21, 30), time(9, 0)), _at(2026, 10, 28, 9, 0)
        )
