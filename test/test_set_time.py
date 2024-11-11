import unittest
from unittest.mock import patch, MagicMock
from callbacks.set_time import set_time

class TestSetTime(unittest.TestCase):
    @patch('callbacks.set_time.update_bot_last_message_id_on_db')
    @patch('callbacks.set_time.print_new_summary')
    @patch('callbacks.set_time.format_summary')
    @patch('callbacks.set_time.find_all_info_by_chat_id')
    @patch('callbacks.set_time.get_sender_name')
    @patch('callbacks.set_time.update_time_on_db')
    @patch('callbacks.set_time.find_row_by_chat_id')
    def test_set_time(self, mock_find_row_by_chat_id, mock_update_time_on_db, mock_get_sender_name, mock_find_all_info_by_chat_id, mock_format_summary, mock_print_new_summary, mock_update_bot_last_message_id_on_db):
        mock_update = MagicMock()
        mock_context = MagicMock()

        # Test case 1: row is None
        with self.subTest("Row is None"):
            mock_find_row_by_chat_id.return_value = None
            set_time(mock_update, mock_context)
            mock_find_row_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_context.bot.send_message.assert_called_once_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
            )

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        mock_context.bot.send_message.reset_mock()

        # Test case 2: no arguments provided
        with self.subTest("No arguments provided"):
            mock_find_row_by_chat_id.return_value = "row"
            mock_context.args = []
            set_time(mock_update, mock_context)
            mock_find_row_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_context.bot.send_message.assert_called_once_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Non hai inserito l'orario: scrivi /settime <orario>"
            )

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        mock_context.bot.send_message.reset_mock()

        # Test case 3: valid arguments provided and print new summary
        with self.subTest("Valid arguments provided and print new summary"):
            mock_find_row_by_chat_id.return_value = "row"
            mock_context.args = ["20:00"]
            mock_find_all_info_by_chat_id.return_value = (["@player1", "@player2"], "Monday", "20:00", "10", "default_message", "pitch", None, None)
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)
            mock_get_sender_name.return_value = "John"
            
            set_time(mock_update, mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_update_time_on_db.assert_called_once_with(mock_update.message.chat_id, "20:00")
            mock_context.bot.send_message.assert_called_once_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Ok, @John! Ho impostato l'orario della partita alle 20:00"
            )
            mock_find_all_info_by_chat_id.assert_called_with(mock_update.message.chat_id)
            mock_format_summary.assert_called_once_with(["@player1", "@player2"], "Monday", "20:00", "10", "default_message", "pitch")
            mock_print_new_summary.assert_called_once_with("formatted_summary", mock_update, mock_context)
            mock_update_bot_last_message_id_on_db.assert_called_once_with(mock_update.message.chat_id, 123)

if __name__ == '__main__':
    unittest.main()
