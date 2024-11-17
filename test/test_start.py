import unittest
from unittest.mock import patch, MagicMock
from callbacks.start import start

class TestStart(unittest.TestCase):

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

    @patch('callbacks.start.create_chat_id_row')
    @patch('callbacks.start.find_all_info_by_chat_id')
    def test_start(self, mock_find_all_info_by_chat_id, mock_create_chat_id_row):

        # Test case 1: row is None
        with self.subTest("Row is None"):
            mock_find_all_info_by_chat_id.return_value = None

            start(self.mock_update, self.mock_context)

            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_create_chat_id_row.assert_called_once_with(self.mock_update.message.chat_id)
            self.assert_send_message_called_once_with(
                "Ciao bestie 😎, chi c'è per il prossimo calcetto? \n"
                "\n"
                "- se sei in forse scrivi _proponimi_, \n"
                "- se vuoi proporre qualcuno scrivi _proponi <nome>_, \n"
                "- per essere aggiunto o confermato rispondi _aggiungimi_,\n"
                "- per aggiungere o confermare qualcuno usa _aggiungi <nome>_,\n"
                "- per essere rimosso _toglimi_, \n"
                "- per rimuovere qualcuno _togli <nome>_, \n"
                "- per modificare le squadre scrivi _scambia <nome 1> con <nome 2>_. \n\n"
                "Posso anche pinnare i messaggi se vuoi "
                "ma per farlo ricordati di aggiungermi come amministratore."
            )

        # Reset mocks for the next subtest
        mock_find_all_info_by_chat_id.reset_mock()
        mock_create_chat_id_row.reset_mock()
        self.mock_context.bot.send_message.reset_mock()

        # Test case 2: row is not None
        with self.subTest("Row is not None"):
            mock_find_all_info_by_chat_id.return_value = "row"

            start(self.mock_update, self.mock_context)

            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_create_chat_id_row.assert_not_called()
            self.assert_send_message_called_once_with(
                "Ciao bestie 😎, chi c'è per il prossimo calcetto? \n"
                "\n"
                "- se sei in forse scrivi _proponimi_, \n"
                "- se vuoi proporre qualcuno scrivi _proponi <nome>_, \n"
                "- per essere aggiunto o confermato rispondi _aggiungimi_,\n"
                "- per aggiungere o confermare qualcuno usa _aggiungi <nome>_,\n"
                "- per essere rimosso _toglimi_, \n"
                "- per rimuovere qualcuno _togli <nome>_, \n"
                "- per modificare le squadre scrivi _scambia <nome 1> con <nome 2>_. \n\n"
                "Posso anche pinnare i messaggi se vuoi "
                "ma per farlo ricordati di aggiungermi come amministratore."
            )

if __name__ == '__main__':
    unittest.main()