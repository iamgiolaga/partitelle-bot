import unittest
from unittest.mock import patch, MagicMock
from callbacks.stop import stop


class TestStop(unittest.TestCase):

    def setUp(self):
        self.mock_update = MagicMock()
        self.mock_context = MagicMock()
        self.mock_update.message.chat_id = 12345
        self.mock_update.effective_chat.id = 12345

    def assert_send_message_called_once_with(self, text):
        self.mock_context.bot.send_message.assert_called_once_with(
            chat_id=self.mock_update.effective_chat.id, parse_mode="markdown", text=text
        )

    @patch("callbacks.stop.delete_row_on_db")
    @patch("callbacks.stop.find_row_by_chat_id")
    def test_stop(self, mock_find_row_by_chat_id, mock_delete_row_on_db):

        # Test case 1: row is None
        with self.subTest("Row is None"):
            mock_find_row_by_chat_id.return_value = None

            stop(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(
                self.mock_update.message.chat_id
            )
            mock_delete_row_on_db.assert_not_called()
            self.assert_send_message_called_once_with(
                "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
            )

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()

        # Test case 2: row is not None
        with self.subTest("Row is not None"):
            mock_find_row_by_chat_id.return_value = "row"

            stop(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(
                self.mock_update.message.chat_id
            )
            mock_delete_row_on_db.assert_called_once_with(
                self.mock_update.message.chat_id
            )
            self.assert_send_message_called_once_with("Ho cancellato la partita.")


if __name__ == "__main__":
    unittest.main()
