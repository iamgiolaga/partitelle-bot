import unittest
from telegram import Update
from unittest.mock import patch, MagicMock
from datetime import datetime
from utils.utils import (
    get_next_weekday,
    compute_next_wednesday,
    get_sender_name,
    swap_players,
    generate_teams,
    flatten_args,
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
