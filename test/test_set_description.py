import unittest
from unittest.mock import patch, MagicMock
from callbacks.set_description import set_description

class TestSetDescription(unittest.TestCase):
    @patch('callbacks.set_description.update_bot_last_message_id_on_db')
    @patch('callbacks.set_description.print_new_summary')
    @patch('callbacks.set_description.format_summary')
    @patch('callbacks.set_description.find_all_info_by_chat_id')
    @patch('callbacks.set_description.get_sender_name')
    @patch('callbacks.set_description.update_description_on_db')
    @patch('callbacks.set_description.find_row_by_chat_id')
    def test_set_description(self, mock_find_row_by_chat_id, mock_update_description_on_db, mock_get_sender_name, mock_find_all_info_by_chat_id, mock_format_summary, mock_print_new_summary, mock_update_bot_last_message_id_on_db):
        mock_update = MagicMock()
        mock_context = MagicMock()

        # Test case 1: row is None
        with self.subTest("Row is None"):
            mock_find_row_by_chat_id.return_value = None
            set_description(mock_update, mock_context)
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
            set_description(mock_update, mock_context)
            mock_find_row_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_context.bot.send_message.assert_called_once_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Non hai inserito la descrizione: scrivi /setdescription <descrizione>"
            )

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        mock_context.bot.send_message.reset_mock()

        # Test case 3: valid arguments provided and print new summary
        with self.subTest("Valid arguments provided and print new summary"):
            mock_find_row_by_chat_id.return_value = "row"
            mock_context.args = ["This is a description"]
            mock_find_all_info_by_chat_id.return_value = (["@player1", "@player2"], "day", "time", "target", "default_message", "pitch", None, None)
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)
            mock_get_sender_name.return_value = "John"
            
            set_description(mock_update, mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_update_description_on_db.assert_called_once_with(mock_update.message.chat_id, "This is a description\n")
            mock_get_sender_name.assert_called_once_with(mock_update)
            mock_find_all_info_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_format_summary.assert_called_once_with(["@player1", "@player2"], "day", "time", "target", "default_message", "pitch")
            mock_print_new_summary.assert_called_once_with("formatted_summary", mock_update, mock_context)
            mock_context.bot.send_message.assert_called_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Ok, @John! Ho aggiornato la descrizione!"
            )
            mock_update_bot_last_message_id_on_db.assert_called_once_with(mock_update.message.chat_id, 123)

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        mock_context.bot.send_message.reset_mock()
        mock_update_description_on_db.reset_mock()
        mock_get_sender_name.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_bot_last_message_id_on_db.reset_mock()

        # Test case 4: valid arguments provided and edit summary
        with self.subTest("Valid arguments provided and edit summary"):
            mock_find_row_by_chat_id.return_value = "row"
            mock_context.args = ["This is a description"]
            mock_find_all_info_by_chat_id.return_value = (["@player1", "@player2"], "day", "time", "target", "default_message", "pitch", None, 123)
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)
            mock_get_sender_name.return_value = "John"
            
            set_description(mock_update, mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_update_description_on_db.assert_called_once_with(mock_update.message.chat_id, "This is a description\n")
            mock_get_sender_name.assert_called_once_with(mock_update)
            mock_find_all_info_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_format_summary.assert_called_once_with(["@player1", "@player2"], "day", "time", "target", "default_message", "pitch")
            mock_print_new_summary.assert_not_called()
            mock_context.bot.send_message.assert_called_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Ok, @John! Ho aggiornato la descrizione!"
            )
            mock_update_bot_last_message_id_on_db.assert_not_called()

if __name__ == '__main__':
    unittest.main()