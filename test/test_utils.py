import unittest
from telegram import Update
from unittest.mock import patch, MagicMock
from datetime import datetime, time
from utils.utils import (
    get_next_weekday,
    compute_next_wednesday,
    extract_match_day,
    normalize_match_time,
    get_sender_name,
    swap_players,
    generate_teams,
    flatten_args,
    parse_names,
    join_names,
    is_command_name,
    exclude_maybe,
    format_teams,
    format_summary,
)


class TestUtils(unittest.TestCase):
    def test_get_next_weekday(self):
        # Test case 1: Start date is a Monday, looking for next Wednesday
        self.assertEqual(get_next_weekday("01/11/2021", 2), "03/11/2021")

        # Test case 2: Start date is a Friday, looking for next Monday
        self.assertEqual(get_next_weekday("05/11/2021", 0), "08/11/2021")

        # Test case 3: Start date is a Sunday, looking for next Sunday
        self.assertEqual(get_next_weekday("07/11/2021", 6), "14/11/2021")

        # Test case 4: Start date is a Wednesday, looking for next Wednesday
        self.assertEqual(get_next_weekday("03/11/2021", 2), "10/11/2021")

        # Test case 5: Start date is a Saturday, looking for next Friday
        self.assertEqual(get_next_weekday("06/11/2021", 4), "12/11/2021")

    def test_get_next_weekday_considers_the_match_time(self):
        match_time = time(20, 0)
        # Wednesday before, at and after the match time
        for hour, minute, expected in [
            (8, 0, "10/11/2021"),
            (19, 59, "10/11/2021"),
            (20, 0, "17/11/2021"),
            (20, 1, "17/11/2021"),
            (23, 59, "17/11/2021"),
        ]:
            now = datetime(2021, 11, 10, hour, minute)
            self.assertEqual(
                get_next_weekday("10/11/2021", 2, now, match_time), expected
            )
        # The time is irrelevant on the other days
        now = datetime(2021, 11, 11, 8, 0)
        self.assertEqual(
            get_next_weekday("11/11/2021", 2, now, match_time), "17/11/2021"
        )
        now = datetime(2021, 11, 9, 23, 0)
        self.assertEqual(
            get_next_weekday("09/11/2021", 2, now, match_time), "10/11/2021"
        )

    @patch("utils.utils.datetime")
    def test_compute_next_wednesday_with_the_match_time(self, mock_date):
        mock_date.strptime = datetime.strptime
        mock_date.today.return_value = datetime(2021, 11, 10, 19, 59)  # Wednesday
        self.assertEqual(compute_next_wednesday("20:00"), "10/11/2021")
        # From the match time on, it is the following week
        mock_date.today.return_value = datetime(2021, 11, 10, 20, 0)
        self.assertEqual(compute_next_wednesday("20:00"), "17/11/2021")
        mock_date.today.return_value = datetime(2021, 11, 10, 20, 1)
        self.assertEqual(compute_next_wednesday("20:00"), "17/11/2021")
        # An unreadable time falls back to the following Wednesday
        mock_date.today.return_value = datetime(2021, 11, 10, 8, 0)
        self.assertEqual(compute_next_wednesday("stasera"), "17/11/2021")

    @patch("utils.utils.datetime")
    def test_compute_next_wednesday(self, mock_date):
        # Test case 1: Today is Monday
        mock_date.today.return_value = datetime(2021, 11, 8)  # Monday
        mock_date.strptime = datetime.strptime
        mock_date.strftime = datetime.strftime
        self.assertEqual(compute_next_wednesday(), "10/11/2021")

        # Test case 2: Today is Tuesday
        mock_date.today.return_value = datetime(2021, 11, 9)  # Tuesday
        mock_date.strptime = datetime.strptime
        mock_date.strftime = datetime.strftime
        self.assertEqual(compute_next_wednesday(), "10/11/2021")

        # Test case 3: Today is Wednesday
        mock_date.today.return_value = datetime(2021, 11, 10)  # Wednesday
        mock_date.strptime = datetime.strptime
        mock_date.strftime = datetime.strftime
        self.assertEqual(compute_next_wednesday(), "17/11/2021")

        # Test case 4: Today is Thursday
        mock_date.today.return_value = datetime(2021, 11, 11)  # Thursday
        mock_date.strptime = datetime.strptime
        mock_date.strftime = datetime.strftime
        self.assertEqual(compute_next_wednesday(), "17/11/2021")

        # Test case 5: Today is Friday
        mock_date.today.return_value = datetime(2021, 11, 12)  # Friday
        mock_date.strptime = datetime.strptime
        mock_date.strftime = datetime.strftime
        self.assertEqual(compute_next_wednesday(), "17/11/2021")

    def test_extract_match_day(self):
        # The default day written by the bot: Italian weekday + dd/mm/yyyy
        self.assertEqual(
            extract_match_day("Mercoledì 28/10/2026"), datetime(2026, 10, 28)
        )
        self.assertEqual(
            extract_match_day("mercoledi 28/10/2026"), datetime(2026, 10, 28)
        )
        self.assertEqual(extract_match_day("SABATO 31/10/2026"), datetime(2026, 10, 31))
        # With the time appended, as trigger_payment_reminder does
        self.assertEqual(
            extract_match_day("Mercoledì 28/10/2026 21:30"),
            datetime(2026, 10, 28, 21, 30),
        )
        # A plain date keeps working
        self.assertEqual(extract_match_day("25/10/2026"), datetime(2026, 10, 25))
        # Unreadable days are still -1
        self.assertEqual(extract_match_day("Mercoledì"), -1)
        self.assertEqual(extract_match_day("sabato 20:00"), -1)
        self.assertEqual(extract_match_day("prossima settimana"), -1)

    def test_normalize_match_time(self):
        for text, expected in [
            ("21:30", "21:30"),
            ("9:30", "09:30"),
            ("0:00", "00:00"),
            ("23:59", "23:59"),
            ("21.30", "21:30"),
            ("9.05", "09:05"),
            (" 21:30 ", "21:30"),
        ]:
            self.assertEqual(normalize_match_time(text), expected)
        for text in ["25:99", "24:00", "21:60", "stasera", "alle 21", "21", "21:5", ""]:
            self.assertIsNone(normalize_match_time(text))

    def test_get_sender_name(self):
        mock_update = MagicMock(spec=Update)
        mock_update.message.from_user.username = "JohnDoe"
        self.assertEqual(get_sender_name(mock_update), "johndoe")

    def test_swap_players(self):
        # Test case 1: Swap two players from different teams
        teams = {
            "black": ["JohnDoe", "JaneDoe", "Alice"],
            "white": ["Bob", "Charlie", "Eve"],
        }
        x = "JohnDoe"
        y = "Bob"
        new_teams = swap_players(teams, x, y)
        self.assertEqual(
            new_teams,
            '{"black": ["Bob", "JaneDoe", "Alice"], "white": ["JohnDoe", "Charlie", "Eve"]}',
        )

        # Test case 2: Swap two players from the same team
        teams = {
            "black": ["JohnDoe", "JaneDoe", "Alice"],
            "white": ["Bob", "Charlie", "Eve"],
        }
        x = "JohnDoe"
        y = "JaneDoe"
        with self.assertRaises(Exception):
            swap_players(teams, x, y)

    @patch("utils.utils.random.sample")
    def test_generate_teams(self, mock_sample):
        players = ["JohnDoe", "JaneDoe", "Alice", "Bob", "Charlie", "Eve"]

        # Mock the output of random.sample
        mock_sample.return_value = ["JohnDoe", "JaneDoe", "Alice"]

        expected_result = '{"black": ["JohnDoe", "JaneDoe", "Alice"], "white": ["Bob", "Charlie", "Eve"]}'
        result = generate_teams(players)
        self.assertEqual(result, expected_result)

    def test_flatten_args(self):
        # Test case 1: Single argument
        args = ["Wednesday"]
        self.assertEqual(flatten_args(args), "Wednesday")

        # Test case 2: Multiple arguments
        args = ["Wednesday", "01/01/2000"]
        self.assertEqual(flatten_args(args), "Wednesday 01/01/2000")

        # Test case 3: No arguments
        args = []
        self.assertEqual(flatten_args(args), "")

    def test_parse_names(self):
        self.assertEqual(parse_names(" luca"), ["luca"])
        self.assertEqual(parse_names(" luca rossi"), ["luca rossi"])
        self.assertEqual(parse_names("a,b,c"), ["a", "b", "c"])
        self.assertEqual(parse_names("  a , b,, ,c ,"), ["a", "b", "c"])
        self.assertEqual(parse_names(""), [])
        self.assertEqual(parse_names("  "), [])
        self.assertEqual(parse_names(" , ,"), [])

    def test_join_names(self):
        self.assertEqual(join_names([]), "")
        self.assertEqual(join_names(["a"]), "a")
        self.assertEqual(join_names(["a", "b"]), "a e b")
        self.assertEqual(join_names(["a", "b", "c"]), "a, b e c")
        self.assertEqual(join_names(["a", "b", "c", "d"]), "a, b, c e d")

    def test_is_command_name(self):
        self.assertTrue(is_command_name("/start"))
        self.assertFalse(is_command_name("luca"))
        self.assertFalse(is_command_name("lu/ca"))

    def test_exclude_maybe(self):
        # Test case 1: No placeholders
        players = ["JohnDoe", "JaneDoe", "Alice", "Bob", "Charlie", "Eve"]
        self.assertEqual(exclude_maybe(players), players)

        # Test case 2: Placeholders present
        players = [
            "JohnDoe",
            "JaneDoe",
            "Alice%is%maybe%present",
            "Bob",
            "Charlie",
            "Eve%is%maybe%present",
        ]
        self.assertEqual(
            exclude_maybe(players), ["JohnDoe", "JaneDoe", "Bob", "Charlie"]
        )

    def test_format_teams(self):
        # Test case 1: Teams are empty
        teams = "{}"
        with self.assertRaises(Exception):
            format_teams(teams)

        # Test case 2: Teams are not empty
        teams = '{"black": ["JohnDoe", "JaneDoe", "Alice"], "white": ["Bob", "Charlie", "Eve"]}'
        self.assertEqual(
            format_teams(teams),
            "*SQUADRA NERA* \n - JohnDoe\n - JaneDoe\n - Alice\n\n*SQUADRA BIANCA* \n - Bob\n - Charlie\n - Eve\n",
        )

    def test_format_summary(self):
        # Test case 1: No players
        all_players = []
        day = "Wednesday"
        time = "20:00"
        target = 6
        default_message = "Default message"
        pitch = "Pitch"
        expected_output = (
            "*GIORNO*: Wednesday | 20:00\n\n"
            "1. ❌\n"
            "2. ❌\n"
            "3. ❌\n"
            "4. ❌\n"
            "5. ❌\n"
            "6. ❌\n\n"
            "Default message\n\n"
            "*CAMPO*: \n"
            "Pitch"
        )
        self.assertEqual(
            format_summary(all_players, day, time, target, default_message, pitch),
            expected_output,
        )

        # Test case 2: Full players present
        all_players = ["JohnDoe", "JaneDoe", "Alice", "Bob", "Charlie", "Eve"]
        day = "Wednesday"
        time = "20:00"
        target = 6
        default_message = "Default message"
        pitch = "Pitch"
        expected_output = (
            "*GIORNO*: Wednesday | 20:00\n\n"
            "1. JohnDoe ✅\n"
            "2. JaneDoe ✅\n"
            "3. Alice ✅\n"
            "4. Bob ✅\n"
            "5. Charlie ✅\n"
            "6. Eve ✅\n\n"
            "Default message\n\n"
            "*CAMPO*: \n"
            "Pitch"
        )
        self.assertEqual(
            format_summary(all_players, day, time, target, default_message, pitch),
            expected_output,
        )

        # Test case 3: Some players present
        all_players = ["JohnDoe", "JaneDoe", "Alice", "Bob", "Charlie"]
        day = "Wednesday"
        time = "20:00"
        target = 6
        default_message = "Default message"
        pitch = "Pitch"
        expected_output = (
            "*GIORNO*: Wednesday | 20:00\n\n"
            "1. JohnDoe ✅\n"
            "2. JaneDoe ✅\n"
            "3. Alice ✅\n"
            "4. Bob ✅\n"
            "5. Charlie ✅\n"
            "6. ❌\n\n"
            "Default message\n\n"
            "*CAMPO*: \n"
            "Pitch"
        )
        self.assertEqual(
            format_summary(all_players, day, time, target, default_message, pitch),
            expected_output,
        )

        # Test case 4: Some players present, some maybe
        all_players = [
            "JohnDoe",
            "JaneDoe",
            "Alice%is%maybe%present",
            "Bob",
            "Charlie%is%maybe%present",
        ]
        day = "Wednesday"
        time = "20:00"
        target = 6
        default_message = "Default message"
        pitch = "Pitch"
        expected_output = (
            "*GIORNO*: Wednesday | 20:00\n\n"
            "1. JohnDoe ✅\n"
            "2. JaneDoe ✅\n"
            "3. Alice ❓\n"
            "4. Bob ✅\n"
            "5. Charlie ❓\n"
            "6. ❌\n\n"
            "Default message\n\n"
            "*CAMPO*: \n"
            "Pitch"
        )
        self.assertEqual(
            format_summary(all_players, day, time, target, default_message, pitch),
            expected_output,
        )


if __name__ == "__main__":
    unittest.main()
