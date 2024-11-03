import unittest
from unittest.mock import patch, MagicMock, call
from callbacks.echo import echo

class TestEcho(unittest.TestCase):

    def setUp(self):
        self.mock_update = MagicMock()
        self.mock_context = MagicMock()
        self.mock_update.message.chat_id = 12345
        self.mock_update.effective_chat.id = 12345
        self.mock_update.message.text = ""

    def assert_send_message_called_once_with(self, text):
        self.mock_context.bot.send_message.assert_called_once_with(
            chat_id=self.mock_update.effective_chat.id,
            parse_mode='markdown',
            text=text
        )

    @patch('callbacks.echo.trigger_payment_reminder')
    @patch('callbacks.echo.edit_summary')
    @patch('callbacks.echo.update_bot_last_message_id_on_db')
    @patch('callbacks.echo.print_new_summary')
    @patch('callbacks.echo.format_summary')
    @patch('callbacks.echo.find_all_info_by_chat_id')
    @patch('callbacks.echo.update_teams_on_db')
    @patch('callbacks.echo.update_players_on_db')
    @patch('callbacks.echo.is_already_present')
    @patch('callbacks.echo.get_sender_name')
    @patch('callbacks.echo.find_row_by_chat_id')
    def test_echo(self, mock_find_row_by_chat_id, mock_get_sender_name, mock_is_already_present, mock_update_players_on_db, mock_update_teams_on_db, mock_find_all_info_by_chat_id, mock_format_summary, mock_print_new_summary, mock_update_bot_last_message_id_on_db, mock_edit_summary, mock_trigger_payment_reminder):

        # Test case 1: row is None
        with self.subTest("Row is None"):
            self.mock_update.message.text = "aggiungimi"
            mock_find_row_by_chat_id.return_value = None

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assert_send_message_called_once_with(
                "Prima di iniziare con le danze, avvia una partita, per farlo usa /start"
            )

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()

        # Test case 2: aggiungimi - already present
        with self.subTest("aggiungimi - already present"):
            self.mock_update.message.text = "aggiungimi"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.return_value = (["@John", "@player2"], "day", "time", 10, "default_message", "pitch", None, None)
            mock_get_sender_name.return_value = "John"
            mock_is_already_present.return_value = True

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_get_sender_name.assert_called_once_with(self.mock_update)
            mock_is_already_present.assert_called_once_with(self.mock_update.message.chat_id, "@John")
            self.assert_send_message_called_once_with(
                "Ma @John, sei già nella lista"
            )

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_get_sender_name.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()

        # Test case 3: aggiungimi - not present
        with self.subTest("aggiungimi - not present"):
            self.mock_update.message.text = "aggiungimi"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2"], "day", "time", 10, "default_message", "pitch", None, None),
                (["@player1", "@player2", "@John"], "day", "time", 10, "default_message", "pitch", None, None)
            ]
            mock_get_sender_name.return_value = "John"
            mock_is_already_present.side_effect = [False, False]
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_find_all_info_by_chat_id.call_count, 2)
            mock_get_sender_name.assert_called_once_with(self.mock_update)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John%is%maybe%present")
            mock_update_players_on_db.assert_called_once_with(self.mock_update.message.chat_id, "@John", "add")
            self.assert_send_message_called_once_with(
                "Ok, @John, ti aggiungo"
            )
            mock_format_summary.assert_called_once_with(["@player1", "@player2", "@John"], "day", "time", 10, "default_message", "pitch")
            mock_print_new_summary.assert_called_once_with("formatted_summary", self.mock_update, self.mock_context)
            mock_update_bot_last_message_id_on_db.assert_called_once_with(self.mock_update.message.chat_id, 123)
            mock_edit_summary.assert_not_called()
            mock_trigger_payment_reminder.assert_not_called()

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_get_sender_name.reset_mock()
        mock_is_already_present.reset_mock()
        mock_update_players_on_db.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_bot_last_message_id_on_db.reset_mock()
        mock_edit_summary.reset_mock()
        mock_trigger_payment_reminder.reset_mock()

        # Test case 4: aggiungimi - not present - edit summary
        with self.subTest("aggiungimi - not present - edit summary"):
            self.mock_update.message.text = "aggiungimi"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2"], "day", "time", 10, "default_message", "pitch", None, 123),
                (["@player1", "@player2", "@John"], "day", "time", 10, "default_message", "pitch", None, 123)
            ]
            mock_get_sender_name.return_value = "John"
            mock_is_already_present.side_effect = [False, False]
            mock_format_summary.return_value = "formatted_summary"

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_find_all_info_by_chat_id.call_count, 2)
            mock_get_sender_name.assert_called_once_with(self.mock_update)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John%is%maybe%present")
            mock_update_players_on_db.assert_called_once_with(self.mock_update.message.chat_id, "@John", "add")
            self.assert_send_message_called_once_with(
                "Ok, @John, ti aggiungo"
            )
            mock_format_summary.assert_called_once_with(["@player1", "@player2", "@John"], "day", "time", 10, "default_message", "pitch")
            mock_edit_summary.assert_called_once_with("formatted_summary", 123, self.mock_update, self.mock_context)
            mock_print_new_summary.assert_not_called()
            mock_update_bot_last_message_id_on_db.assert_not_called()
            mock_trigger_payment_reminder.assert_not_called()

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_get_sender_name.reset_mock()
        mock_is_already_present.reset_mock()
        mock_update_players_on_db.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_bot_last_message_id_on_db.reset_mock()
        mock_edit_summary.reset_mock()
        mock_trigger_payment_reminder.reset_mock()

        # Test case 5: aggiungimi - not present - match full
        with self.subTest("aggiungimi - not present - match full"):
            self.mock_update.message.text = "aggiungimi"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2", "@player3"], "day", "time", 3, "default_message", "pitch", None, None)
            ]
            mock_get_sender_name.return_value = "John"
            mock_is_already_present.side_effect = [False, False]

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_get_sender_name.assert_called_once_with(self.mock_update)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John%is%maybe%present")
            self.assert_send_message_called_once_with(
                "Siete già in 3"
            )

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_get_sender_name.reset_mock()
        mock_is_already_present.reset_mock()
        mock_update_players_on_db.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_bot_last_message_id_on_db.reset_mock()
        mock_edit_summary.reset_mock()
        mock_trigger_payment_reminder.reset_mock()

        # Test case 6: aggiungimi - not present - reached target
        with self.subTest("aggiungimi - not present - reached target"):
            self.mock_update.message.text = "aggiungimi"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2"], "day", "time", 3, "default_message", "pitch", None, 123),
                (["@player1", "@player2", "@John"], "day", "time", 3, "default_message", "pitch", None, 123)
            ]
            mock_get_sender_name.return_value = "John"
            mock_is_already_present.side_effect = [False, False]
            mock_format_summary.return_value = "formatted_summary"

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_find_all_info_by_chat_id.call_count, 2)
            mock_get_sender_name.assert_called_once_with(self.mock_update)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John%is%maybe%present")
            self.mock_context.bot.send_message.assert_has_calls([
                call(
                    chat_id=self.mock_update.effective_chat.id,
                    parse_mode='markdown',
                    text="Ok, @John, ti aggiungo"
                ),
                call(
                    chat_id=self.mock_update.effective_chat.id,
                    parse_mode='markdown',
                    text="🚀 *SI GIOCA* 🚀 facciamo le squadre? /teams 😎"
                )
            ])
            mock_update_players_on_db.assert_called_once_with(self.mock_update.message.chat_id, "@John", "add")
            mock_format_summary.assert_called_once_with(["@player1", "@player2", "@John"], "day", "time", 3, "default_message", "pitch")
            mock_edit_summary.assert_called_once_with("formatted_summary", 123, self.mock_update, self.mock_context)
            mock_print_new_summary.assert_not_called()
            mock_update_bot_last_message_id_on_db.assert_not_called()
            mock_trigger_payment_reminder.assert_called_once_with(self.mock_update, self.mock_context, "day", "time")

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_get_sender_name.reset_mock()
        mock_is_already_present.reset_mock()
        mock_update_players_on_db.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_bot_last_message_id_on_db.reset_mock()
        mock_edit_summary.reset_mock()
        mock_trigger_payment_reminder.reset_mock()

        # Test case 7: aggiungimi - maybe present - confirmation
        with self.subTest("aggiungimi - maybe present confirmation"):
            self.mock_update.message.text = "aggiungimi"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2", "@John%is%maybe%present"], "day", "time", 10, "default_message", "pitch", None, None),
                (["@player1", "@player2", "@John"], "day", "time", 10, "default_message", "pitch", None, None)
            ]
            mock_get_sender_name.return_value = "John"
            mock_is_already_present.side_effect = [False, True]

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_find_all_info_by_chat_id.call_count, 2)
            mock_get_sender_name.assert_called_once_with(self.mock_update)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John%is%maybe%present")
            self.assert_send_message_called_once_with(
                "Ok, @John, ti confermo"
            )
            mock_update_players_on_db.assert_has_calls([
                call(self.mock_update.message.chat_id, "@John%is%maybe%present", "remove"),
                call(self.mock_update.message.chat_id, "@John", "add")
            ])
            mock_format_summary.assert_called_once_with(["@player1", "@player2", "@John"], "day", "time", 10, "default_message", "pitch")
            mock_print_new_summary.assert_called_once_with("formatted_summary", self.mock_update, self.mock_context)
            mock_update_bot_last_message_id_on_db.assert_called_once_with(self.mock_update.message.chat_id, 123)
            mock_edit_summary.assert_not_called()
            mock_trigger_payment_reminder.assert_not_called()

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_get_sender_name.reset_mock()
        mock_is_already_present.reset_mock()
        mock_update_players_on_db.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_bot_last_message_id_on_db.reset_mock()
        mock_edit_summary.reset_mock()
        mock_trigger_payment_reminder.reset_mock()

        # Test case 8: aggiungi - already present
        with self.subTest("aggiungi - already present"):
            self.mock_update.message.text = "aggiungi @John"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [(["@John", "@player2"], "day", "time", 10, "default_message", "pitch", None, None)]
            mock_is_already_present.side_effect = [True]

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_is_already_present.assert_called_once_with(self.mock_update.message.chat_id, "@john")
            self.assert_send_message_called_once_with(
                "@john è già nella lista"
            )
        
        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        
        # Test case 9: aggiungi - not present
        with self.subTest("aggiungi - not present"):
            self.mock_update.message.text = "aggiungi @John"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2"], "day", "time", 10, "default_message", "pitch", None, None),
                (["@player1", "@player2", "@John"], "day", "time", 10, "default_message", "pitch", None, None)
            ]
            mock_is_already_present.side_effect = [False, False]
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_find_all_info_by_chat_id.call_count, 2)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@john")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@john%is%maybe%present")
            mock_format_summary.assert_called_once_with(["@player1", "@player2", "@John"], "day", "time", 10, "default_message", "pitch")
            mock_print_new_summary.assert_called_once_with("formatted_summary", self.mock_update, self.mock_context)
            self.assert_send_message_called_once_with(
                "Ok, aggiungo @john"
            )
            mock_update_players_on_db.assert_called_once_with(self.mock_update.message.chat_id, "@john", "add")
            mock_update_bot_last_message_id_on_db.assert_called_once_with(self.mock_update.message.chat_id, 123)
            mock_trigger_payment_reminder.assert_not_called()
        
        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_players_on_db.reset_mock()
        mock_update_bot_last_message_id_on_db.reset_mock()
        mock_trigger_payment_reminder.reset_mock()

        # Test case 10: proponimi - already maybe present
        with self.subTest("proponimi - already maybe present"):
            self.mock_update.message.text = "proponimi"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [(["@John", "@player2"], "day", "time", 10, "default_message", "pitch", None, None)]
            mock_is_already_present.side_effect = [True]

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_is_already_present.assert_called_once_with(self.mock_update.message.chat_id, "@John%is%maybe%present")
            self.assert_send_message_called_once_with(
                "Ma @John, sei già in forse"
            )

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()

        # Test case 11: proponimi - not present
        with self.subTest("proponimi - not present"):
            self.mock_update.message.text = "proponimi"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2"], "day", "time", 10, "default_message", "pitch", None, None),
                (["@player1", "@player2", "@John%is%maybe%present"], "day", "time", 10, "default_message", "pitch", None, None)
            ]
            mock_is_already_present.side_effect = [False, False]
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_find_all_info_by_chat_id.call_count, 2)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John%is%maybe%present")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John")
            mock_format_summary.assert_called_once_with(["@player1", "@player2", "@John%is%maybe%present"], "day", "time", 10, "default_message", "pitch")
            mock_print_new_summary.assert_called_once_with("formatted_summary", self.mock_update, self.mock_context)
            self.assert_send_message_called_once_with(
                "Ok, @John, ti propongo"
            )
            mock_update_players_on_db.assert_called_once_with(self.mock_update.message.chat_id, "@John%is%maybe%present", "add")
            mock_update_bot_last_message_id_on_db.assert_called_once_with(self.mock_update.message.chat_id, 123)
            mock_trigger_payment_reminder.assert_not_called()

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_players_on_db.reset_mock()
        mock_update_bot_last_message_id_on_db.reset_mock()
        mock_trigger_payment_reminder.reset_mock()

        # Test case 12: proponimi - not present - match full
        with self.subTest("proponimi - not present - match full"):
            self.mock_update.message.text = "proponimi"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2", "@player3"], "day", "time", 3, "default_message", "pitch", None, None)
            ]
            mock_is_already_present.side_effect = [False, False]

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John%is%maybe%present")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John")
            self.assert_send_message_called_once_with(
                "Siete già in 3"
            )
        
        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()

        # Test case 13: proponimi - present - becoming maybe present
        with self.subTest("proponimi - present - becoming maybe present"):
            self.mock_update.message.text = "proponimi"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2", "@John"], "day", "time", 3, "default_message", "pitch", None, 123),
                (["@player1", "@player2", "@John%is%maybe%present"], "day", "time", 3, "default_message", "pitch", None, 123)
            ]
            mock_is_already_present.side_effect = [False, True]
            mock_format_summary.return_value = "formatted_summary"

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_find_all_info_by_chat_id.call_count, 2)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John%is%maybe%present")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John")
            self.assert_send_message_called_once_with(
                "Ok, @John, ti metto in forse"
            )
            mock_update_players_on_db.assert_has_calls([
                call(self.mock_update.message.chat_id, "@John", "remove"),
                call(self.mock_update.message.chat_id, "@John%is%maybe%present", "add")
            ])
            mock_format_summary.assert_called_once_with(["@player1", "@player2", "@John%is%maybe%present"], "day", "time", 3, "default_message", "pitch")
            mock_edit_summary.assert_called_once_with("formatted_summary", 123, self.mock_update, self.mock_context)
            mock_print_new_summary.assert_not_called()
            mock_update_bot_last_message_id_on_db.assert_not_called()
            mock_trigger_payment_reminder.assert_not_called()

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_players_on_db.reset_mock()
        mock_edit_summary.reset_mock()

        # Test case 14: proponi - already present
        with self.subTest("proponi - already present"):
            self.mock_update.message.text = "proponi @John"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [(["@John", "@player2"], "day", "time", 10, "default_message", "pitch", None, None)]
            mock_is_already_present.side_effect = [True]

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_is_already_present.assert_called_once_with(self.mock_update.message.chat_id, "@john%is%maybe%present")
            self.assert_send_message_called_once_with(
                "@john è già nella lista"
            )

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()

        # Test case 15: proponi - not present
        with self.subTest("proponi - not present"):
            self.mock_update.message.text = "proponi @John"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2"], "day", "time", 10, "default_message", "pitch", None, None),
                (["@player1", "@player2", "@John%is%maybe%present"], "day", "time", 10, "default_message", "pitch", None, None)
            ]
            mock_is_already_present.side_effect = [False, False]
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_find_all_info_by_chat_id.call_count, 2)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@john%is%maybe%present")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@john")
            mock_format_summary.assert_called_once_with(["@player1", "@player2", "@John%is%maybe%present"], "day", "time", 10, "default_message", "pitch")
            mock_print_new_summary.assert_called_once_with("formatted_summary", self.mock_update, self.mock_context)
            self.assert_send_message_called_once_with(
                "Ok, propongo @john"
            )
            mock_update_players_on_db.assert_called_once_with(self.mock_update.message.chat_id, "@john%is%maybe%present", "add")
            mock_update_bot_last_message_id_on_db.assert_called_once_with(self.mock_update.message.chat_id, 123)
            mock_trigger_payment_reminder.assert_not_called()

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_players_on_db.reset_mock()
        mock_update_bot_last_message_id_on_db.reset_mock()
        mock_trigger_payment_reminder.reset_mock()

        # Test case 16: proponi - present - becoming maybe present
        with self.subTest("proponi - present - becoming maybe present"):
            self.mock_update.message.text = "proponi @John"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2", "@john"], "day", "time", 5, "default_message", "pitch", None, 123),
                (["@player1", "@player2", "@john%is%maybe%present"], "day", "time", 5, "default_message", "pitch", None, 123)
            ]
            mock_is_already_present.side_effect = [False, True]
            mock_format_summary.return_value = "formatted_summary"

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_find_all_info_by_chat_id.call_count, 2)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@john%is%maybe%present")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@john")
            self.assert_send_message_called_once_with(
                "Va bene, metto in forse @john"
            )
            mock_update_players_on_db.assert_has_calls([
                call(self.mock_update.message.chat_id, "@john", "remove"),
                call(self.mock_update.message.chat_id, "@john%is%maybe%present", "add")
            ])
            mock_format_summary.assert_called_once_with(["@player1", "@player2", "@john%is%maybe%present"], "day", "time", 5, "default_message", "pitch")
            mock_edit_summary.assert_called_once_with("formatted_summary", 123, self.mock_update, self.mock_context)
            mock_print_new_summary.assert_not_called()
            mock_update_bot_last_message_id_on_db.assert_not_called()
            mock_trigger_payment_reminder.assert_not_called()

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_get_sender_name.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_players_on_db.reset_mock()
        mock_edit_summary.reset_mock()

        # Test case 17: proponi - present - becoming maybe present - revoked teams
        with self.subTest("proponi - present - becoming maybe present - revoked teams"):
            self.mock_update.message.text = "proponi @John"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2", "@john"], "day", "time", 3, "default_message", "pitch", "teams", 123),
                (["@player1", "@player2", "@john%is%maybe%present"], "day", "time", 3, "default_message", "pitch", "teams", 123)
            ]
            mock_is_already_present.side_effect = [False, True]
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_find_all_info_by_chat_id.call_count, 2)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@john%is%maybe%present")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@john")
            self.mock_context.bot.send_message.assert_has_calls([
                call(
                    chat_id=self.mock_update.effective_chat.id,
                    parse_mode='markdown',
                    text="Va bene, metto in forse @john"
                ),
                call(
                    chat_id=self.mock_update.effective_chat.id,
                    parse_mode='markdown',
                    text="*SQUADRE ANNULLATE*"
                )
            ])
            mock_update_players_on_db.assert_has_calls([
                call(self.mock_update.message.chat_id, "@john", "remove"),
                call(self.mock_update.message.chat_id, "@john%is%maybe%present", "add")
            ])
            mock_update_teams_on_db.assert_called_once_with(self.mock_update.message.chat_id, None)
            mock_format_summary.assert_called_once_with(["@player1", "@player2", "@john%is%maybe%present"], "day", "time", 3, "default_message", "pitch")
            mock_edit_summary.assert_called_once_with("formatted_summary", 123, self.mock_update, self.mock_context)
            mock_print_new_summary.assert_not_called()
            mock_update_bot_last_message_id_on_db.assert_not_called()
            mock_trigger_payment_reminder.assert_not_called()

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_get_sender_name.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_players_on_db.reset_mock()
        mock_edit_summary.reset_mock()
        mock_update_teams_on_db.reset_mock()

        # Test case 18: toglimi - not present
        with self.subTest("toglimi - not present"):
            self.mock_update.message.text = "toglimi"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [(["@player1", "@player2"], "day", "time", 10, "default_message", "pitch", None, None)]
            mock_is_already_present.side_effect = [False, False]
            mock_get_sender_name.return_value = "John"

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_get_sender_name.assert_called_once_with(self.mock_update)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John%is%maybe%present")
            self.assert_send_message_called_once_with(
                "Non eri in lista neanche prima"
            )

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_get_sender_name.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        
        # Test case 19: toglimi - present
        with self.subTest("toglimi - present"):
            self.mock_update.message.text = "toglimi"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2", "@John"], "day", "time", 10, "default_message", "pitch", None, None),
                (["@player1", "@player2"], "day", "time", 10, "default_message", "pitch", None, None)
            ]
            mock_is_already_present.side_effect = [True]
            mock_get_sender_name.return_value = "John"
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_find_all_info_by_chat_id.call_count, 2)
            mock_is_already_present.assert_called_once_with(self.mock_update.message.chat_id, "@John")
            self.assert_send_message_called_once_with(
                "Mamma mia... che paccaro"
            )
            mock_update_players_on_db.assert_called_once_with(self.mock_update.message.chat_id, "@John", "remove")
            mock_format_summary.assert_called_once_with(["@player1", "@player2"], "day", "time", 10, "default_message", "pitch")
            mock_print_new_summary.assert_called_once_with("formatted_summary", self.mock_update, self.mock_context)
            mock_update_bot_last_message_id_on_db.assert_called_once_with(self.mock_update.message.chat_id, 123)
            mock_trigger_payment_reminder.assert_not_called()

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_players_on_db.reset_mock()
        mock_update_bot_last_message_id_on_db.reset_mock()
        mock_trigger_payment_reminder.reset_mock()

        # Test case 20: toglimi - maybe present
        with self.subTest("toglimi - maybe present"):
            self.mock_update.message.text = "toglimi"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2", "@John%is%maybe%present"], "day", "time", 10, "default_message", "pitch", None, None),
                (["@player1", "@player2"], "day", "time", 10, "default_message", "pitch", None, None)
            ]
            mock_is_already_present.side_effect = [False, True]
            mock_get_sender_name.return_value = "John"
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_find_all_info_by_chat_id.call_count, 2)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John%is%maybe%present")
            self.assert_send_message_called_once_with(
                "Peccato, un po' ci avevo sperato"
            )
            mock_update_players_on_db.assert_called_once_with(self.mock_update.message.chat_id, "@John%is%maybe%present", "remove")
            mock_format_summary.assert_called_once_with(["@player1", "@player2"], "day", "time", 10, "default_message", "pitch")
            mock_print_new_summary.assert_called_once_with("formatted_summary", self.mock_update, self.mock_context)
            mock_update_bot_last_message_id_on_db.assert_called_once_with(self.mock_update.message.chat_id, 123)
            mock_trigger_payment_reminder.assert_not_called()

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_players_on_db.reset_mock()
        mock_update_bot_last_message_id_on_db.reset_mock()
        mock_trigger_payment_reminder.reset_mock()

        # Test case 21: toglimi - maybe present - revoked teams
        with self.subTest("toglimi - maybe present - revoked teams"):
            self.mock_update.message.text = "toglimi"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [
                (["@player1", "@player2", "@John%is%maybe%present"], "day", "time", 3, "default_message", "pitch", "teams", 123),
                (["@player1", "@player2"], "day", "time", 3, "default_message", "pitch", "teams", 123)
            ]
            mock_is_already_present.side_effect = [False, True]
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_find_all_info_by_chat_id.call_count, 2)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@John%is%maybe%present")
            self.mock_context.bot.send_message.assert_has_calls([
                call(
                    chat_id=self.mock_update.effective_chat.id,
                    parse_mode='markdown',
                    text="Peccato, un po' ci avevo sperato"
                ),
                call(
                    chat_id=self.mock_update.effective_chat.id,
                    parse_mode='markdown',
                    text="*SQUADRE ANNULLATE*"
                )
            ])
            mock_update_players_on_db.assert_called_once_with(self.mock_update.message.chat_id, "@John%is%maybe%present", "remove")
            mock_update_teams_on_db.assert_called_once_with(self.mock_update.message.chat_id, None)
            mock_format_summary.assert_called_once_with(["@player1", "@player2"], "day", "time", 3, "default_message", "pitch")
            mock_print_new_summary.assert_not_called()
            mock_update_bot_last_message_id_on_db.assert_not_called()
            mock_trigger_payment_reminder.assert_not_called()

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset_mock()
        mock_update_players_on_db.reset_mock()
        mock_update_teams_on_db.reset_mock()

        # Test case 22: scambia - no teams
        with self.subTest("scambia - no teams"):
            self.mock_update.message.text = "scambia @John con @player1"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [(["@player1", "@player2", "@John"], "day", "time", 10, "default_message", "pitch", None, None)]
            mock_is_already_present.return_value = False

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_is_already_present.assert_not_called()
            self.assert_send_message_called_once_with(
                "Per usare questa funzionalità devi prima formare delle squadre con /teams"
            )
        
        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()

        # Test case 23: scambia - y not present
        with self.subTest("scambia - y not present"):
            self.mock_update.message.text = "scambia @John con @player3"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [(["@player1", "@player2"], "day", "time", 10, "default_message", "pitch", {"black": ["@John"], "white": ["@player1", "@player2"]}, 123)]
            mock_is_already_present.side_effect = [True, False]

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@john")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@player3")
            self.assert_send_message_called_once_with(
                "@player3 non c'è"
            )

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()

        # Test case 24: scambia - x not present
        with self.subTest("scambia - x not present"):
            self.mock_update.message.text = "scambia @John con @player3"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [(["@player1", "@player2"], "day", "time", 10, "default_message", "pitch", {"black": ["@player1", "@player2"], "white": ["@John"]}, 123)]
            mock_is_already_present.side_effect = [False, True]

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_is_already_present.assert_called_once_with(self.mock_update.message.chat_id, "@john")
            self.assert_send_message_called_once_with(
                "@john non c'è"
            )

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()

        # Test case 25: scambia - x and y in the same team
        with self.subTest("scambia - x and y in the same team"):
            self.mock_update.message.text = "scambia @John con @player2"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [(["@player1", "@player2", "@player3, @john"], "day", "time", 4, "default_message", "pitch", {"black": ["@john", "@player2"], "white": ["@player1", "@player3"]}, 123)]
            mock_is_already_present.side_effect = [True, True]
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@john")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@player2")
            self.assert_send_message_called_once_with(
                "@john e @player2 sono nella stessa squadra!"
            )
            mock_update_teams_on_db.assert_not_called()
            mock_trigger_payment_reminder.assert_not_called()

        # Reset mocks for the next subtest
        mock_find_row_by_chat_id.reset_mock()
        self.mock_context.bot.send_message.reset_mock()
        mock_is_already_present.reset_mock()
        mock_find_all_info_by_chat_id.reset_mock()
        mock_format_summary.reset_mock()
        mock_print_new_summary.reset
        mock_update_teams_on_db.reset_mock()
        mock_trigger_payment_reminder.reset_mock()

        # Test case 26: scambia - x and y present
        with self.subTest("scambia - x and y present"):
            self.mock_update.message.text = "scambia @John con @player1"
            mock_find_row_by_chat_id.return_value = "row"
            mock_find_all_info_by_chat_id.side_effect = [(["@player1", "@player2", "@player3, @john"], "day", "time", 4, "default_message", "pitch", {"black": ["@john", "@player2"], "white": ["@player1", "@player3"]}, 123)]
            mock_is_already_present.side_effect = [True, True]
            mock_format_summary.return_value = "formatted_summary"
            mock_print_new_summary.return_value = MagicMock(message_id=123)

            echo(self.mock_update, self.mock_context)

            mock_find_row_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            mock_find_all_info_by_chat_id.assert_called_once_with(self.mock_update.message.chat_id)
            self.assertEqual(mock_is_already_present.call_count, 2)
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@john")
            mock_is_already_present.assert_any_call(self.mock_update.message.chat_id, "@player1")
            self.assert_send_message_called_once_with(
                "Perfetto, ho scambiato @john con @player1"
            )
            mock_update_teams_on_db.assert_called_once_with(self.mock_update.message.chat_id, '{"black": ["@player1", "@player2"], "white": ["@john", "@player3"]}')
            mock_trigger_payment_reminder.assert_not_called()
if __name__ == '__main__':
    unittest.main()