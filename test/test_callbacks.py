import unittest
from unittest.mock import patch, MagicMock
from callbacks.help_func import help_func
from callbacks.participants import participants
from callbacks.set_day import set_day

class TestCallbacks(unittest.TestCase):

    @patch('callbacks.help_func.CallbackContext')
    def test_help_func(self, mock_context_class):
        mock_update = MagicMock()
        mock_context = MagicMock()
        mock_context_class.return_value = mock_context

        help_func(mock_update, mock_context)

        mock_context.bot.send_message.assert_called_once_with(
            chat_id=mock_update.effective_chat.id,
            parse_mode='markdown',
            text="Ecco a te la lista completa dei comandi di questo bot: \n"
                 "- se sei in forse scrivi _proponimi_, \n"
                 "- se vuoi proporre qualcuno scrivi _proponi <nome>_, \n"
                 "- per essere aggiunto o confermato rispondi _aggiungimi_,\n"
                 "- per aggiungere o confermare qualcuno usa _aggiungi <nome>_,\n"
                 "- per essere rimosso _toglimi_, \n"
                 "- per rimuovere qualcuno _togli <nome>_, \n"
                 "- per modificare le squadre scrivi _scambia <nome 1> con <nome 2>_. \n\n"
                 "Posso anche pinnare i messaggi se vuoi "
                 "ma per farlo ricordati di aggiungermi come amministratore.\n"
                 "\n"
                 "/start - Crea una nuova partita \n"
                 "/setnumber - Imposta il numero di partecipanti \n"
                 "/setday - Imposta il giorno della partita \n"
                 "/settime - Imposta l’orario della partita \n"
                 "/setdescription - Imposta la descrizione sotto i partecipanti \n"
                 "/setpitch - Imposta il campo \n"
                 "/participants - Mostra i partecipanti della partita attuale \n"
                 "/teams - Mostra le squadre della partita attuale \n"
                 "/stop - Rimuovi la partita \n"
                 "/help - Mostra la lista di comandi disponibili"
        )

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
            mock_find_all_info_by_chat_id.return_value = ("player1, player2", "day", "time", "target", "default_message", "pitch", None, None)
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)

            participants(mock_update, mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_find_all_info_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_format_summary.assert_called_once_with("player1, player2", "day", "time", "target", "default_message", "pitch")
            mock_print_new_summary.assert_called_once_with("formatted_summary", mock_update, mock_context)
            mock_context.bot.send_message.assert_not_called()
            mock_update_bot_last_message_id_on_db.assert_called_once_with(mock_update.message.chat_id, 123)

    @patch('callbacks.set_day.update_bot_last_message_id_on_db')
    @patch('callbacks.set_day.print_new_summary')
    @patch('callbacks.set_day.format_summary')
    @patch('callbacks.set_day.find_all_info_by_chat_id')
    @patch('callbacks.set_day.get_sender_name')
    @patch('callbacks.set_day.update_day_on_db')
    @patch('callbacks.set_day.find_row_by_chat_id')
    def test_set_day(self, mock_find_row_by_chat_id, mock_update_day_on_db, mock_get_sender_name, mock_find_all_info_by_chat_id, mock_format_summary, mock_print_new_summary, mock_update_bot_last_message_id_on_db):
        mock_update = MagicMock()
        mock_context = MagicMock()

        # Test case 1: row is None
        with self.subTest("Row is None"):
            mock_find_row_by_chat_id.return_value = None
            set_day(mock_update, mock_context)
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
            set_day(mock_update, mock_context)
            mock_find_row_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_context.bot.send_message.assert_called_once_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Non hai inserito il giorno: scrivi /setday <giorno>"
            )

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        mock_context.bot.send_message.reset_mock()

        # Test case 3: valid arguments provided
        with self.subTest("Valid arguments provided"):
            mock_find_row_by_chat_id.return_value = "row"
            mock_context.args = ["Monday"]
            mock_find_all_info_by_chat_id.return_value = ("player1, player2", "Monday", "20:00", "10", "default_message", "pitch", None, None)
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)
            mock_get_sender_name.return_value = "John"
            
            set_day(mock_update, mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_update_day_on_db.assert_called_once_with(mock_update.message.chat_id, "Monday")
            mock_get_sender_name.assert_called_once_with(mock_update)
            self.assertEqual(mock_find_all_info_by_chat_id.call_count, 2)
            mock_find_all_info_by_chat_id.assert_called_with(mock_update.message.chat_id)
            mock_format_summary.assert_called_once_with("player1, player2", "Monday", "20:00", "10", "default_message", "pitch")
            mock_print_new_summary.assert_called_once_with("formatted_summary", mock_update, mock_context)
            mock_context.bot.send_message.assert_called_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Ok, @John! Ho impostato il giorno della partita il Monday"
            )
            mock_update_bot_last_message_id_on_db.assert_called_once_with(mock_update.message.chat_id, 123)

if __name__ == '__main__':
    unittest.main()