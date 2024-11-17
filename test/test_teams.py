import unittest
from unittest.mock import patch, MagicMock
from callbacks.teams import teams

class TestTeams(unittest.TestCase):

    def setUp(self):
        self.mock_update = MagicMock()
        self.mock_context = MagicMock()
        self.mock_update.message.chat_id = 12345
        self.mock_update.effective_chat.id = 12345

    def assert_send_message_called_once_with(self, text):
        self.mock_context.bot.send_message.assert_called_once_with(
            chat_id=self.mock_update.effective_chat.id,
            parse_mode='markdown',
            text=text
        )

    @patch('callbacks.teams.update_teams_on_db')
    @patch('callbacks.teams.generate_teams')
    @patch('callbacks.teams.format_teams')
    @patch('callbacks.teams.exclude_maybe')
    @patch('callbacks.teams.find_all_info_by_chat_id')
    def test_teams(self, mock_find_all_info_by_chat_id, mock_exclude_maybe, mock_format_teams, mock_generate_teams, mock_update_teams_on_db):

        # Test case 1: row is None
        with self.subTest("Row is None"):
            mock_find_all_info_by_chat_id.return_value = None

            teams(self.mock_update, self.mock_context)

            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assert_send_message_called_once_with(
                "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
            )

        # Reset mocks for the next subtest
        mock_find_all_info_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()

        # Test case 2: players is None
        with self.subTest("Players is None"):
            mock_find_all_info_by_chat_id.return_value = (None, None, None, 10, None, None, None, None)

            teams(self.mock_update, self.mock_context)

            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_exclude_maybe.assert_not_called()
            self.assert_send_message_called_once_with(
                "Prima di poter fare le squadre, devi raggiungere 10 partecipanti"
            )

        # Reset mocks for the next subtest
        mock_find_all_info_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()

        # Test case 3: teams is not None
        with self.subTest("Teams is not None"):
            mock_find_all_info_by_chat_id.return_value = (["@player1", "@player2"], None, None, 10, None, None, {"team1": ["@player1"], "team2": ["@player2"]}, None)
            mock_exclude_maybe.return_value = ["@player1", "@player2"]
            mock_format_teams.return_value = "Formatted teams"

            teams(self.mock_update, self.mock_context)

            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_exclude_maybe.assert_called_once_with(["@player1", "@player2"])
            mock_format_teams.assert_called_once_with('{"team1": ["@player1"], "team2": ["@player2"]}')
            self.assert_send_message_called_once_with("Formatted teams")

        # Reset mocks for the next subtest
        mock_find_all_info_by_chat_id.reset_mock()
        mock_exclude_maybe.reset_mock()
        mock_format_teams.reset_mock()
        self.mock_context.bot.send_message.reset_mock()

        # Test case 4: target is not even
        with self.subTest("Target is not even"):
            mock_find_all_info_by_chat_id.return_value = (["@player1", "@player2", "@player3"], None, None, 9, None, None, None, None)
            mock_exclude_maybe.return_value = ["@player1", "@player2", "@player3"]

            teams(self.mock_update, self.mock_context)

            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_exclude_maybe.assert_called_once_with(["@player1", "@player2", "@player3"])
            self.assert_send_message_called_once_with(
                "Per usare questa funzionalità dovete essere in un numero pari di partecipanti"
            )

        # Reset mocks for the next subtest
        mock_find_all_info_by_chat_id.reset_mock()
        mock_exclude_maybe.reset_mock()
        self.mock_context.bot.send_message.reset_mock()

        # Test case 5: reached target
        with self.subTest("Reached target"):
            mock_find_all_info_by_chat_id.return_value = (["@player1", "@player2"], None, None, 2, None, None, None, None)
            mock_exclude_maybe.return_value = ["@player1", "@player2"]
            mock_generate_teams.return_value = {"team1": ["@player1"], "team2": ["@player2"]}
            mock_format_teams.return_value = "Formatted teams"

            teams(self.mock_update, self.mock_context)

            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_exclude_maybe.assert_called_once_with(["@player1", "@player2"])
            mock_generate_teams.assert_called_once_with(["@player1", "@player2"])
            mock_update_teams_on_db.assert_called_once_with(self.mock_update.message.chat_id, {"team1": ["@player1"], "team2": ["@player2"]})
            mock_format_teams.assert_called_once_with({"team1": ["@player1"], "team2": ["@player2"]})
            self.assert_send_message_called_once_with("Formatted teams")

        # Reset mocks for the next subtest
        mock_find_all_info_by_chat_id.reset_mock()
        mock_exclude_maybe.reset_mock()
        mock_generate_teams.reset_mock()
        mock_update_teams_on_db.reset_mock()
        mock_format_teams.reset_mock()
        self.mock_context.bot.send_message.reset_mock()

        # Test case 6: not reached target
        with self.subTest("Not reached target"):
            mock_find_all_info_by_chat_id.return_value = (["@player1"], None, None, 2, None, None, None, None)
            mock_exclude_maybe.return_value = ["@player1"]

            teams(self.mock_update, self.mock_context)

            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_exclude_maybe.assert_called_once_with(["@player1"])
            self.assert_send_message_called_once_with(
                "Prima di poter fare le squadre, devi raggiungere 2 partecipanti"
            )

if __name__ == '__main__':
    unittest.main()