-- Baseline schema of the PartitelleBot database, as created by hand on Render.
-- The table name is configured via PB_DB_TABLE_NAME: `all_players` for prod, `all_players_test` for the test bot
-- (both live in the same database and share the same structure).

CREATE TABLE public.all_players (
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

CREATE TABLE public.all_players_test (
    chat_id int8 NOT NULL,
    players _varchar NULL,
    "day" text NULL,
    "time" text NULL,
    target int4 NULL,
    custom_message text NULL,
    pitch text NULL,
    bot_last_message_id int4 NULL,
    teams json NULL,
    CONSTRAINT all_players_test_pkey PRIMARY KEY (chat_id)
);
