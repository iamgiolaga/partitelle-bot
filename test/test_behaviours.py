import unittest
from unittest.mock import patch, MagicMock
from behaviours.edit_summary import edit_summary
from behaviours.print_new_summary import print_new_summary
from telegram.utils.helpers import escape_markdown


class TestBehaviours(unittest.TestCase):

    @patch("behaviours.edit_summary.CallbackContext")
    def test_edit_summary(self, mock_context_class):
        mock_context = MagicMock()
        mock_context_class.return_value = mock_context
        current_situation = "current_situation"
        last_message_id = 123
        update = MagicMock()
        context = MagicMock()

        edit_summary(current_situation, last_message_id, update, context)

        context.bot.edit_message_text.assert_called_once_with(
            chat_id=update.effective_chat.id,
            message_id=last_message_id,
            parse_mode="markdown",
            text=current_situation,
        )
        context.bot.pin_chat_message.assert_called_once_with(
            chat_id=update.effective_chat.id, message_id=last_message_id
        )

    def test_print_new_summary(self):
        current_situation = "Some message"

        # Test case 1: no markdown error
        with self.subTest("No markdown error"):
            update = MagicMock()
            context = MagicMock()
            msg = print_new_summary(current_situation, update, context)
            context.bot.send_message.assert_called_once_with(
                chat_id=update.effective_chat.id,
                parse_mode="markdown",
                text="Some message",
            )
            context.bot.pin_chat_message.assert_called_once_with(
                chat_id=update.effective_chat.id, message_id=msg.message_id
            )
            self.assertEqual(msg, context.bot.send_message.return_value)

        # Test case 2: markdown error
        with self.subTest("Markdown error"):
            update = MagicMock()
            context = MagicMock()
            mock_response = MagicMock()
            context.bot.send_message.side_effect = [
                Exception("Some error"),
                mock_response,
            ]
            msg = print_new_summary(current_situation, update, context)

            error_message = (
                "Sembra che tu abbia inserito nella descrizione un carattere speciale di telegram (`, *, _).\n"
                "Per favore cambiala con /setdescription <descrizione> assicurandoti di non inserire uno di questi caratteri.\n"
                "Se la tua intenzione era, invece, di formattare il testo, ricordati di usare anche il carattere di chiusura, come in questo *esempio*."
            )

            context.bot.send_message.assert_called_with(
                chat_id=update.effective_chat.id,
                parse_mode="markdown",
                text=escape_markdown(error_message),
            )
            context.bot.pin_chat_message.assert_not_called()
            self.assertEqual(msg, mock_response)

        # Test case 3: error while pinning the message
        with self.subTest("Error while pinning the message"):
            update = MagicMock()
            context = MagicMock()
            context.bot.pin_chat_message.side_effect = Exception("Some error")
            msg = print_new_summary(current_situation, update, context)
            context.bot.send_message.assert_called_once_with(
                chat_id=update.effective_chat.id,
                parse_mode="markdown",
                text="Some message",
            )
            context.bot.pin_chat_message.assert_called_once_with(
                chat_id=update.effective_chat.id, message_id=msg.message_id
            )
            self.assertEqual(msg, context.bot.send_message.return_value)


if __name__ == "__main__":
    unittest.main()
