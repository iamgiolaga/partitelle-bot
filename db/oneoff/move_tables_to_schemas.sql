-- One-time transition from the legacy layout (both tables in `public`) to one schema per environment.
-- Run once on the Render database, with psql, in this order:
--   1. PART 1 (staging), and deploy the staging bot with PB_DB_SCHEMA=staging, PB_DB_TABLE_NAME=all_players
--   2. PART 2 (prod), and deploy the prod bot with PB_DB_SCHEMA=prod, PB_DB_TABLE_NAME=all_players
-- The parts are independent and each one runs in its own transaction.
-- Between the SQL and the deploy of the matching bot, that bot fails (table not found): do them back to back.
-- Afterwards `python -m db.migrate` (run at deploy) records the baseline in <schema>._yoyo_migration:
-- the baseline uses CREATE TABLE IF NOT EXISTS, so it is a no-op on the already existing tables.
-- Data is preserved: ALTER TABLE ... SET SCHEMA / RENAME only change metadata.

-- ===================== PART 1: STAGING (public.all_players_test -> staging.all_players) =====================
BEGIN;
CREATE SCHEMA IF NOT EXISTS staging;
ALTER TABLE public.all_players_test SET SCHEMA staging;
ALTER TABLE staging.all_players_test RENAME TO all_players;
-- RENAME TO does not rename the primary key constraint (and its index), which keeps the old name
-- `all_players_test_pkey`: rename it to match the baseline migration and the other environments.
ALTER TABLE staging.all_players RENAME CONSTRAINT all_players_test_pkey TO all_players_pkey;
COMMIT;

-- ===================== PART 2: PROD (public.all_players -> prod.all_players) =====================
BEGIN;
CREATE SCHEMA IF NOT EXISTS prod;
ALTER TABLE public.all_players SET SCHEMA prod;
COMMIT;
