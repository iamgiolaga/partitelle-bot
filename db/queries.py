from utils.constants import default_target, default_time, table_name, default_message
from psycopg2 import sql
from utils.utils import compute_next_wednesday
from db.cursor import connection

def create_bamboo_chat_id_row(chat_id):
    pitch = "Crespi Sport Village \n" \
            "\n" \
            "Via Carlo Valvassori Peroni, 48, 20133 \n" \
            "Milano, MI, 02 266 3774 \n" \
            "https://g.co/kgs/L9b6KZ"
    default_day = "Mercoledì " + compute_next_wednesday()
    connection.execute(
        sql.SQL("INSERT INTO {table} (chat_id, players, day, time, target, custom_message, pitch, teams, bot_last_message_id) "
            "VALUES ( %s, null, %s, %s, %s, %s, %s, null, null)")
        .format(table=sql.Identifier(table_name)),
        [str(chat_id), default_day, default_time, str(default_target), default_message, pitch]
    )

def delete_row_on_db(chat_id):
    connection.execute(sql.SQL('DELETE FROM {table} WHERE chat_id=%s').format(table=sql.Identifier(table_name)), [str(chat_id)])

def is_already_present(chat_id, name):
    connection.execute(sql.SQL('SELECT players FROM {table} WHERE chat_id=%s').format(table=sql.Identifier(table_name)), [str(chat_id)])
    current_players = connection.fetchone()
    if current_players is None or current_players[0] is None:
        return False
    return name in current_players[0]

def create_chat_id_row(chat_id):
    default_day = "Mercoledì " + compute_next_wednesday()
    connection.execute(
        sql.SQL("INSERT INTO {table} (chat_id, players, day, time, target, custom_message, pitch, teams, bot_last_message_id) "
                       "VALUES ( %s, null, %s, %s, %s, %s, null, null, null)")
        .format(table=sql.Identifier(table_name)),
        [str(chat_id), default_day, default_time, str(default_target), default_message]
    )

def find_all_info_by_chat_id(chat_id):
    connection.execute(
        sql.SQL('SELECT players, day, time, target, custom_message, pitch, teams, bot_last_message_id FROM {table} WHERE chat_id=%s')
        .format(table=sql.Identifier(table_name)), [str(chat_id)]
    )
    return connection.fetchone()

def find_row_by_chat_id(chat_id):
    connection.execute(sql.SQL('SELECT chat_id, players FROM {table} WHERE chat_id=%s').format(table=sql.Identifier(table_name)), [str(chat_id)])
    return connection.fetchone()

def update_bot_last_message_id_on_db(chat_id, msg_id):
    connection.execute(sql.SQL('UPDATE {table} SET bot_last_message_id = %s WHERE chat_id= %s').format(table=sql.Identifier(table_name)), [str(msg_id), str(chat_id)])

def update_target_on_db(chat_id, target):
    connection.execute(sql.SQL('UPDATE {table} SET target = %s WHERE chat_id= %s').format(table=sql.Identifier(table_name)), [str(target), str(chat_id)])

def update_day_on_db(chat_id, day):
    connection.execute(sql.SQL("UPDATE {table} SET day = %s WHERE chat_id= %s").format(table=sql.Identifier(table_name)), [day, str(chat_id)])

def update_time_on_db(chat_id, time):
    connection.execute(sql.SQL("UPDATE {table} SET time = %s WHERE chat_id= %s").format(table=sql.Identifier(table_name)), [time, str(chat_id)])

def update_description_on_db(chat_id, description):
    connection.execute(sql.SQL("UPDATE {table} SET custom_message = %s WHERE chat_id= %s").format(table=sql.Identifier(table_name)), [description, str(chat_id)])

def update_pitch_on_db(chat_id, pitch):
    connection.execute(sql.SQL("UPDATE {table} SET pitch = %s WHERE chat_id= %s").format(table=sql.Identifier(table_name)), [pitch, str(chat_id)])

def update_teams_on_db(chat_id, teams):
    connection.execute(sql.SQL("UPDATE {table} SET teams = %s WHERE chat_id= %s").format(table=sql.Identifier(table_name)), [teams, str(chat_id)])

def update_players_on_db(chat_id, new_entry, action):
    connection.execute(sql.SQL('SELECT players FROM {table} WHERE chat_id=%s').format(table=sql.Identifier(table_name)), [str(chat_id)])
    current_players = connection.fetchone()
    if current_players[0] is None:
        connection.execute(sql.SQL("UPDATE {table} SET players = %s WHERE chat_id=%s").format(table=sql.Identifier(table_name)), ['{'+new_entry+'}', str(chat_id)])
    else:
        result = "{"
        if action == "add":
            current_players[0].append(new_entry)
            for index, player in enumerate(current_players[0]):
                if index < len(current_players):
                    result = result + player + ","
                else:
                    last_char_index = len(result) - 1
                    if result[last_char_index] == "}":
                        result = result[0:last_char_index] + result[last_char_index].replace("}", ",")
                    result = result + player + "}"
        elif action == "remove":
            current_players[0].remove(new_entry)
            for index, player in enumerate(current_players[0]):
                if index < len(current_players[0])-1 and len(current_players[0]) > 1:
                    result = result + player + ","
                else:
                    result = result + player + "}"

            if len(current_players[0]) == 0:
                result = None

        connection.execute(sql.SQL('UPDATE {table} SET players = %s WHERE chat_id=%s').format(table=sql.Identifier(table_name)), [result, str(chat_id)])
