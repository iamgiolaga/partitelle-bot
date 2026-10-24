# Render database: transition and monthly recreation

The production database is a Render free Postgres instance, which must be deleted and recreated every month. Each environment is a schema (`staging`, `prod`) of one user-owned database; the structure comes from `migrations/` (see "Database migrations" in `CONTRIBUTING.md`), so no manual DDL is ever needed.

Fixed values to use whenever the instance is (re)created, so that only host and password change:

| Field | Value |
| --- | --- |
| Name | `partitelle-bot-db` |
| Database | `partitelle` |
| User | `partitelle` |
| Region | EU (Frankfurt) |
| PostgreSQL version | 17 |

Env vars live in the Render environment groups `PB_ENV_VARS` (service `partitelle-bot`, prod) and `PB_TEST_ENV_VARS` (service `partitelle-bot-test`, staging). The `partitelle-bot-stats-tracker` repo reads the prod table through its GitHub Actions secrets `PB_DB_*`.

## A. One-time transition (current instance)

Goal: move from the legacy tables `public.all_players` (prod) and `public.all_players_test` (staging) in the `postgres` database to a user-owned database with the `staging` and `prod` schemas. `CREATE SCHEMA` is not permitted in `postgres`, but the current instance already contains a user-owned database with a generated name that the bots do not use, so this can be done now without waiting for the monthly wipe.

1. **Start command.** On Render set the Start Command of both services to `python -m db.migrate && python main.py`. This is safe immediately: with `PB_DB_SCHEMA` unset, migrations are skipped.
2. **Staging.** In `PB_TEST_ENV_VARS` set `PB_DB_NAME=<generated db name>` (Render dashboard, database, Connections), `PB_DB_SCHEMA=staging`, `PB_DB_TABLE_NAME=all_players`. Run Manual Deploy: it creates `staging.all_players` (empty, test data is not migrated). Smoke test `/start` on the test bot.
3. **Prod, prepare.** From a laptop, run the migrations against the new database using the external connection values:

   ```bash
   PB_DB_HOST=<external host> PB_DB_NAME=<generated db name> PB_DB_USER=<user> \
   PB_DB_PASSWORD=<password> PB_DB_PORT=5432 PB_DB_SCHEMA=prod \
   uv run python -m db.migrate
   ```

   Then copy the data. The Render external URL ends with the database name: use the URL as shown for the generated database, and replace the trailing database name with `/postgres` for the legacy one.

   ```bash
   psql "<external URL, ending in /postgres>" -c "\copy public.all_players TO STDOUT" \
     | psql "<external URL, ending in /<generated db name>>" -c "\copy prod.all_players FROM STDIN"
   ```

   Verify with `SELECT count(*)` on `public.all_players` (legacy) and `prod.all_players` (new): the counts must match.
4. **Prod, switch.** In `PB_ENV_VARS` set `PB_DB_NAME=<generated db name>`, `PB_DB_SCHEMA=prod`, keep `PB_DB_TABLE_NAME=all_players`. Run Manual Deploy and smoke test. Rows written to the old table between steps 3 and 4 are lost, so do the two steps back to back (or `TRUNCATE prod.all_players` and re-copy right before the switch).
5. **Stats tracker.** Update `PB_DB_NAME` and add `PB_DB_SCHEMA=prod` in its secrets. It needs the search_path code change, tracked separately.
6. **Cleanup (optional, later).** Drop the legacy tables in `postgres`.`public`.

## B. Monthly recreation

1. **Export prod data.** Keep the dump private and local: it contains personal data, never commit it.

   ```bash
   pg_dump --data-only --schema=prod "<external URL>" > prod-data-YYYY-MM.sql
   ```

   The client version must be at least the server version. If the local client is older, use Docker:

   ```bash
   docker run --rm postgres:17 pg_dump --data-only --schema=prod "<external URL>" > prod-data-YYYY-MM.sql
   ```

   Dumping the `staging` schema too is usually not needed.
2. **Recreate the instance.** Delete the Render database and create a new one with the fixed values in the table above.
3. **Update env vars.** In `PB_ENV_VARS` and `PB_TEST_ENV_VARS` change only `PB_DB_HOST` (internal host) and `PB_DB_PASSWORD`. Do the same for the stats-tracker secrets.
4. **Deploy.** Manual Deploy staging, then prod: the migrations recreate the schemas and tables.
5. **Restore prod data.**

   ```bash
   psql "<external URL>" -f prod-data-YYYY-MM.sql
   ```

   Or, with an older local client: `docker run --rm -i -v "$PWD":/dump postgres:17 psql "<external URL>" -f /dump/prod-data-YYYY-MM.sql`. Verify that the row count of `prod.all_players` matches the one noted in step 1.
6. **DBeaver.** Connect to the database `partitelle`, not `postgres`.

## C. Troubleshooting

- `permission denied for database` on `CREATE SCHEMA`: you are connected to `postgres` instead of the user-owned database. Check `PB_DB_NAME`.
- `pg_dump: error: aborting because of server version mismatch`: the local client is older than the server. Use the `postgres:17` Docker image.
- Migrations fail at start: the bot does not start (the start command uses `&&`). Check the deploy logs for the failing migration.
