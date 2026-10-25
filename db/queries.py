from conf.conf import table_name
from utils.constants import maybe_placeholder
from psycopg import sql
from db.connection import connection


def is_already_present(chat_id, name):
    with connection() as conn:
        cur = conn.execute(
            sql.SQL("SELECT players FROM {table} WHERE chat_id=%s").format(
                table=sql.Identifier(table_name)
            ),
            [str(chat_id)],
        )
        current_players = cur.fetchone()
        if current_players is None or current_players[0] is None:
            return False
        return name in current_players[0]


def update_bot_last_message_id_on_db(chat_id, msg_id):
    with connection() as conn:
        conn.execute(
            sql.SQL(
                "UPDATE {table} SET bot_last_message_id = %s WHERE chat_id= %s"
            ).format(table=sql.Identifier(table_name)),
            [str(msg_id), str(chat_id)],
        )


def update_target_on_db(chat_id, target):
    with connection() as conn:
        conn.execute(
            sql.SQL("UPDATE {table} SET target = %s WHERE chat_id= %s").format(
                table=sql.Identifier(table_name)
            ),
            [str(target), str(chat_id)],
        )


def update_day_on_db(chat_id, day):
    with connection() as conn:
        conn.execute(
            sql.SQL("UPDATE {table} SET day = %s WHERE chat_id= %s").format(
                table=sql.Identifier(table_name)
            ),
            [day, str(chat_id)],
        )


def update_time_on_db(chat_id, time):
    with connection() as conn:
        conn.execute(
            sql.SQL("UPDATE {table} SET time = %s WHERE chat_id= %s").format(
                table=sql.Identifier(table_name)
            ),
            [time, str(chat_id)],
        )


def update_description_on_db(chat_id, description):
    with connection() as conn:
        conn.execute(
            sql.SQL("UPDATE {table} SET custom_message = %s WHERE chat_id= %s").format(
                table=sql.Identifier(table_name)
            ),
            [description, str(chat_id)],
        )


def update_pitch_on_db(chat_id, pitch):
    with connection() as conn:
        conn.execute(
            sql.SQL("UPDATE {table} SET pitch = %s WHERE chat_id= %s").format(
                table=sql.Identifier(table_name)
            ),
            [pitch, str(chat_id)],
        )


def update_teams_on_db(chat_id, teams):
    with connection() as conn:
        conn.execute(
            sql.SQL("UPDATE {table} SET teams = %s WHERE chat_id= %s").format(
                table=sql.Identifier(table_name)
            ),
            [teams, str(chat_id)],
        )


def update_players_on_db(chat_id, new_entry, action):
    # the players array literal is built by concatenation: an empty entry corrupts it
    # and a /command is never a name; every write path goes through here
    if action == "add" and (
        not new_entry.replace(maybe_placeholder, "").strip()
        or new_entry.startswith("/")
    ):
        raise ValueError("invalid player name: " + repr(new_entry))
    with connection() as conn:
        cur = conn.execute(
            sql.SQL("SELECT players FROM {table} WHERE chat_id=%s").format(
                table=sql.Identifier(table_name)
            ),
            [str(chat_id)],
        )
        current_players = cur.fetchone()
        if current_players[0] is None:
            conn.execute(
                sql.SQL("UPDATE {table} SET players = %s WHERE chat_id=%s").format(
                    table=sql.Identifier(table_name)
                ),
                ["{" + new_entry + "}", str(chat_id)],
            )
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
                            result = result[0:last_char_index] + result[
                                last_char_index
                            ].replace("}", ",")
                        result = result + player + "}"
            elif action == "remove":
                current_players[0].remove(new_entry)
                for index, player in enumerate(current_players[0]):
                    if (
                        index < len(current_players[0]) - 1
                        and len(current_players[0]) > 1
                    ):
                        result = result + player + ","
                    else:
                        result = result + player + "}"

                if len(current_players[0]) == 0:
                    result = None

            conn.execute(
                sql.SQL("UPDATE {table} SET players = %s WHERE chat_id=%s").format(
                    table=sql.Identifier(table_name)
                ),
                [result, str(chat_id)],
            )
