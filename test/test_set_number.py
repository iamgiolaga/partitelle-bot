import unittest
from unittest.mock import patch, MagicMock, call
from callbacks.set_number import set_number

class TestSetNumber(unittest.TestCase):
    @patch('callbacks.set_number.update_bot_last_message_id_on_db')
    @patch('callbacks.set_number.edit_summary')
    @patch('callbacks.set_number.print_new_summary')
    @patch('callbacks.set_number.format_summary')
    @patch('callbacks.set_number.find_all_info_by_chat_id')
    @patch('callbacks.set_number.get_sender_name')
    @patch('callbacks.set_number.update_target_on_db')
    @patch('callbacks.set_number.update_teams_on_db')
    @patch('callbacks.set_number.remove_job_if_exists')
    def test_set_number(self, mock_remove_job_if_exists, mock_update_teams_on_db, mock_update_target_on_db, mock_get_sender_name, mock_find_all_info_by_chat_id, mock_format_summary, mock_print_new_summary, mock_edit_summary, mock_update_bot_last_message_id_on_db):
        mock_update = MagicMock()
        mock_context = MagicMock()

        # Test case 1: row is None
        with self.subTest("Row is None"):
            mock_find_all_info_by_chat_id.return_value = None
            set_number(mock_update, mock_context)
            mock_find_all_info_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_context.bot.send_message.assert_called_once_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
            )

        # Reset mocks for the next subtest
        mock_find_all_info_by_chat_id.reset_mock()
        mock_context.bot.send_message.reset_mock()

        # Test case 2: more than one argument provided
        with self.subTest("More than one argument provided"):
            mock_find_all_info_by_chat_id.return_value = "row"
            mock_context.args = ["1", "2"]
            set_number(mock_update, mock_context)
            mock_find_all_info_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_context.bot.send_message.assert_called_once_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Hai messo più di un numero, probabilmente intendevi /setnumber 1"
            )

        # Reset mocks for the next subtest
        mock_find_all_info_by_chat_id.reset_mock()
        mock_context.bot.send_message.reset_mock()

        # Test case 3: invalid number provided
        with self.subTest("Invalid number provided"):
            mock_find_all_info_by_chat_id.return_value = (["@player1", "@player2"], "Monday", "20:00", "10", "default_message", "pitch", None, None)
            mock_context.args = ["0"]
            mock_get_sender_name.return_value = "John"
            set_number(mock_update, mock_context)
            mock_find_all_info_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_context.bot.send_message.assert_called_once_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Non è un numero valido di partecipanti 🌚"
            )
        
        # Reset mocks for the next subtest
        mock_find_all_info_by_chat_id.reset_mock()
        mock_context.bot.send_message.reset_mock()
        mock_get_sender_name.reset_mock()

        # Test case 4: not a number
        with self.subTest("Not a number"):
            mock_find_all_info_by_chat_id.return_value = (["@player1", "@player2"], "Monday", "20:00", "10", "default_message", "pitch", None, None)
            mock_context.args = ["not_a_number"]
            mock_get_sender_name.return_value = "John"
            set_number(mock_update, mock_context)
            mock_find_all_info_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_context.bot.send_message.assert_called_once_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="@John, quello ti sembra un numero? 😂"
            )

        # Reset mocks for the next subtest
        mock_find_all_info_by_chat_id.reset_mock()
        mock_context.bot.send_message.reset_mock()
        mock_get_sender_name.reset_mock()

        # Test case 5: number less than participants
        with self.subTest("Number less than participants"):
            mock_find_all_info_by_chat_id.return_value = (["@player1", "@player2", "@player3"], "Monday", "20:00", "10", "default_message", "pitch", None, None)
            mock_context.args = ["2"]
            mock_get_sender_name.return_value = "John"
            set_number(mock_update, mock_context)
            mock_find_all_info_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_context.bot.send_message.assert_called_once_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Hai ridotto i partecipanti ma c'è ancora gente nella lista. Io non saprei chi togliere, puoi farlo tu? 🙏"
            )
        
        # Reset mocks for the next subtest
        mock_find_all_info_by_chat_id.reset_mock()
        mock_context.bot.send_message.reset_mock()
        mock_get_sender_name.reset_mock()

        # Test case 6: number less than 2
        with self.subTest("Number less than 2"):
            mock_find_all_info_by_chat_id.return_value = (["@player1", "@player2"], "Monday", "20:00", "10", "default_message", "pitch", None, None)
            mock_context.args = ["1"]
            mock_get_sender_name.return_value = "John"
            set_number(mock_update, mock_context)
            mock_find_all_info_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_context.bot.send_message.assert_called_once_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Il numero che hai inserito non va bene 👎"
            )
        
        # Reset mocks for the next subtest
        mock_find_all_info_by_chat_id.reset_mock()
        mock_context.bot.send_message.reset_mock()
        mock_get_sender_name.reset_mock()

        # Test case 7: teams is not None
        with self.subTest("Teams is not None"):
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2"], "Monday", "20:00", "10", "default_message", "pitch", "teams", 123),
                (["@player1", "@player2"], "Monday", "20:00", "8", "default_message", "pitch", None, 123)
            ]
            mock_context.args = ["8"]
            mock_get_sender_name.return_value = "John"
            mock_format_summary.return_value = "formatted_summary"
            set_number(mock_update, mock_context)
            mock_find_all_info_by_chat_id.assert_has_calls([
                call(mock_update.message.chat_id), 
                call(mock_update.message.chat_id)
            ])
            mock_get_sender_name.assert_called_once_with(mock_update)
            mock_update_teams_on_db.assert_called_once_with(mock_update.message.chat_id, None)
            mock_remove_job_if_exists.assert_called_once_with(str(mock_update.message.chat_id), mock_context)
            mock_update_target_on_db.assert_called_once_with(mock_update.message.chat_id, 8)
            mock_format_summary.assert_called_once_with(["@player1", "@player2"], "Monday", "20:00", "8", "default_message", "pitch")
            mock_context.bot.send_message.assert_has_calls([
                call(chat_id=mock_update.effective_chat.id, parse_mode='markdown', text="*SQUADRE ANNULLATE*"),
                call(chat_id=mock_update.effective_chat.id, parse_mode='markdown', text="Ok, @John! Ho impostato il numero di partecipanti a 8")
            ])
            mock_edit_summary.assert_called_once_with("formatted_summary", 123, mock_update, mock_context)

        # Reset mocks for the next subtest
        mock_update_teams_on_db.reset_mock()
        mock_remove_job_if_exists.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_update_target_on_db.reset_mock()
        mock_get_sender_name.reset_mock()
        mock_format_summary.reset_mock()
        mock_edit_summary.reset_mock()
        mock_context.bot.send_message.reset_mock()

        # Test case 8: reached target
        with self.subTest("Reached target"):
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2"], "Monday", "20:00", "4", "default_message", "pitch", None, None),
                (["@player1", "@player2"], "Monday", "20:00", "2", "default_message", "pitch", None, None)
            ]
            mock_context.args = ["2"]
            mock_get_sender_name.return_value = "John"
            mock_print_new_summary.return_value = MagicMock(message_id=123)
            set_number(mock_update, mock_context)
            mock_find_all_info_by_chat_id.assert_has_calls([
                call(mock_update.message.chat_id), 
                call(mock_update.message.chat_id)
            ])
            mock_update_target_on_db.assert_called_once_with(mock_update.message.chat_id, 2)
            mock_get_sender_name.assert_called_once_with(mock_update)
            mock_format_summary.assert_called_once_with(["@player1", "@player2"], "Monday", "20:00", "2", "default_message", "pitch")
            mock_print_new_summary.assert_called_once_with("formatted_summary", mock_update, mock_context)
            mock_context.bot.send_message.assert_has_calls([
                call(chat_id=mock_update.effective_chat.id, parse_mode='markdown', text="🚀 *SI GIOCA* 🚀 facciamo le squadre? /teams 😎"),
                call(chat_id=mock_update.effective_chat.id, parse_mode='markdown', text="Ok, @John! Ho impostato il numero di partecipanti a 2")
            ])
            mock_update_bot_last_message_id_on_db.assert_called_once_with(mock_update.message.chat_id, 123)

        # Reset mocks for the next subtest
        mock_update_teams_on_db.reset_mock()
        mock_remove_job_if_exists.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_update_target_on_db.reset_mock()
        mock_get_sender_name.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_bot_last_message_id_on_db.reset_mock()
        mock_context.bot.send_message.reset_mock()

        # Test case 9: /setnumber without an argument
        with self.subTest("/setnumber without an argument"):
            mock_find_all_info_by_chat_id.side_effect = [(["@player1", "@player2"], "Monday", "20:00", "10", "default_message", "pitch", None, None)]
            mock_context.args = []
            set_number(mock_update, mock_context)
            mock_find_all_info_by_chat_id.assert_called_once_with(mock_update.message.chat_id)
            mock_context.bot.send_message.assert_called_once_with(
                chat_id=mock_update.effective_chat.id,
                parse_mode='markdown',
                text="Non hai inserito il numero: scrivi /setnumber <numero>"
            )

if __name__ == '__main__':
    unittest.main()
