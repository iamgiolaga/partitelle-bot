import unittest
from unittest.mock import patch, MagicMock
from callbacks.participants import participants

class TestParticipants(unittest.TestCase):
    @patch('callbacks.participants.update_bot_last_message_id_on_db')
    @patch('callbacks.participants.print_new_summary')
    @patch('callbacks.participants.format_summary')
    @patch('callbacks.participants.find_all_info_by_chat_id')
    @patch('callbacks.participants.find_row_by_chat_id')
    def test_participants(self, mock_find_row_by_chat_id, mock_find_all_info_by_chat_id, mock_format_summary, mock_print_new_summary, mock_update_bot_last_message_id_on_db):
        mock_update = MagicMock()
        mock_context = MagicMock()

        # Test case 1: row is None
        with self.subTest("Row is None"):
            mock_find_row_by_chat_id.return_value = None
            participants(mock_update, mock_context)
            mock_find_row_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_context.bot.send_message.assert_called_once_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
            )

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        mock_context.bot.send_message.reset_mock()

        # Test case 2: row is not None
        with self.subTest("Row is not None"):
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.return_value = (["@player1", "@player2"], "day", "time", "target", "default_message", "pitch", None, None)
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)

            participants(mock_update, mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_find_all_info_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_format_summary.assert_called_once_with(["@player1", "@player2"], "day", "time", "target", "default_message", "pitch")
            mock_print_new_summary.assert_called_once_with("formatted_summary", mock_update, mock_context)
            mock_context.bot.send_message.assert_not_called()
            mock_update_bot_last_message_id_on_db.assert_called_once_with(mock_update.message.chat_id, 123)

if __name__ == '__main__':
    unittest.main()
