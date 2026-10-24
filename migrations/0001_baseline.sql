-- depends:
-- Baseline: the table as it was created by hand on Render.
-- Unqualified name: it lands in the schema of the connection's search_path (PB_DB_SCHEMA).
-- IF NOT EXISTS: on the environments moved by db/oneoff/move_tables_to_schemas.sql the table already exists.
-- No rollback on purpose: dropping the table would delete production data.
CREATE TABLE IF NOT EXISTS all_players (
    chat_id int8 NOT NULL,
    players _varchar NULL,
    "day" text NULL,
    "time" text NULL,
    target int4 NULL,
    custom_message text NULL,
    pitch text NULL,
    bot_last_message_id int4 NULL,
    teams json NULL,
    CONSTRAINT all_players_pkey PRIMARY KEY (chat_id)
);
