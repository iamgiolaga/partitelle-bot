-- depends: 0001_baseline
-- Normalized schema, created next to all_players (which stays the source of truth until the data copy and the code switch).
-- Unqualified names: they land in the schema of the connection's search_path (PB_DB_SCHEMA).
-- No rollback, like 0001: the tables will hold production data once the bot writes to them.
CREATE TYPE participant_status AS ENUM ('confirmed', 'maybe', 'waiting');
CREATE TYPE team_colour AS ENUM ('black', 'white');
CREATE TYPE bot_language AS ENUM ('it');

CREATE FUNCTION set_updated_ts() RETURNS trigger AS $$
BEGIN
    NEW.updated_ts = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE chat (
    chat_uuid uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    created_ts timestamptz NOT NULL DEFAULT now(),
    updated_ts timestamptz NOT NULL DEFAULT now(),
    telegram_chat_id bigint NOT NULL UNIQUE
);

CREATE TABLE setting (
    setting_uuid uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    created_ts timestamptz NOT NULL DEFAULT now(),
    updated_ts timestamptz NOT NULL DEFAULT now(),
    chat_uuid uuid NOT NULL UNIQUE REFERENCES chat ON DELETE CASCADE,
    language bot_language NOT NULL DEFAULT 'it',
    timezone text NOT NULL DEFAULT 'Europe/Rome',
    default_target smallint NOT NULL DEFAULT 10 CHECK (default_target BETWEEN 2 AND 40),
    -- ISO weekday: 1 = Monday, 3 = Wednesday, 7 = Sunday
    default_weekday smallint NOT NULL DEFAULT 3 CHECK (default_weekday BETWEEN 1 AND 7),
    default_time time NOT NULL DEFAULT '20:00',
    default_pitch text NULL,
    default_description text NULL
);

CREATE TABLE match (
    match_uuid uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    created_ts timestamptz NOT NULL DEFAULT now(),
    updated_ts timestamptz NOT NULL DEFAULT now(),
    chat_uuid uuid NOT NULL REFERENCES chat ON DELETE CASCADE,
    starts_ts timestamptz NOT NULL,
    target smallint NOT NULL CHECK (target BETWEEN 2 AND 40),
    description text NULL,
    pitch text NULL,
    telegram_summary_message_id bigint NULL,
    telegram_reminder_message_id bigint NULL,
    reminder_sent_ts timestamptz NULL,
    stopped_ts timestamptz NULL
);

-- At most one active match per chat; also serves the lookup of the active match.
CREATE UNIQUE INDEX match_one_active_per_chat_idx ON match (chat_uuid) WHERE stopped_ts IS NULL;
-- Match history of a chat, newest first; also covers the chat_uuid foreign key (cascading deletes).
CREATE INDEX match_chat_uuid_starts_ts_idx ON match (chat_uuid, starts_ts DESC);

CREATE TABLE participant (
    participant_uuid uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    created_ts timestamptz NOT NULL DEFAULT now(),
    updated_ts timestamptz NOT NULL DEFAULT now(),
    match_uuid uuid NOT NULL REFERENCES match ON DELETE CASCADE,
    telegram_user_id bigint NULL,
    display_name text NULL,
    status participant_status NOT NULL,
    position integer NOT NULL,
    team team_colour NULL,
    CONSTRAINT participant_team_only_if_confirmed CHECK (team IS NULL OR status = 'confirmed')
);

CREATE UNIQUE INDEX participant_match_display_name_idx ON participant (match_uuid, lower(display_name)) WHERE display_name IS NOT NULL;
CREATE UNIQUE INDEX participant_match_telegram_user_idx ON participant (match_uuid, telegram_user_id) WHERE telegram_user_id IS NOT NULL;
CREATE INDEX participant_match_uuid_idx ON participant (match_uuid);

CREATE TRIGGER chat_set_updated_ts BEFORE UPDATE ON chat FOR EACH ROW EXECUTE FUNCTION set_updated_ts();
CREATE TRIGGER setting_set_updated_ts BEFORE UPDATE ON setting FOR EACH ROW EXECUTE FUNCTION set_updated_ts();
CREATE TRIGGER match_set_updated_ts BEFORE UPDATE ON match FOR EACH ROW EXECUTE FUNCTION set_updated_ts();
CREATE TRIGGER participant_set_updated_ts BEFORE UPDATE ON participant FOR EACH ROW EXECUTE FUNCTION set_updated_ts();

CREATE VIEW active_match AS SELECT * FROM match WHERE stopped_ts IS NULL;
