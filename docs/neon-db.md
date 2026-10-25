# Neon database

The database is hosted on Neon Free (it used to be a Render free Postgres that expired every month, see [#79](https://github.com/iamgiolaga/partitelle-bot/issues/79)). There is one Neon project per environment, so each has its own free quota (100 CU-hours/month). Each environment uses a schema (`staging`, `prod`) of the database `partitelle`; the structure comes from `migrations/` (see "Database migrations" in `CONTRIBUTING.md`), so no manual DDL is ever needed.

| Field | Value |
| --- | --- |
| Projects | one for staging, one for prod |
| Region | AWS Europe Central 1 (Frankfurt) |
| PostgreSQL version | 17 |
| Database | `partitelle` |
| Role | `partitelle_owner` |
| Expiry | none |
| Idle | scales to zero after 5 minutes, wakes on the next connection |

## Connecting

In the Neon console, open the project, click Connect and turn "Connection pooling" OFF: use the **direct** host (no `-pooler` in it). The pooled host rejects the `-c search_path` startup option that `db/connection.py` and yoyo use to select the schema.

## Env vars

Set in the Render environment groups `PB_ENV_VARS` (service `partitelle-bot`, prod) and `PB_TEST_ENV_VARS` (service `partitelle-bot-test`, staging):

| Var | Value |
| --- | --- |
| `PB_DB_HOST` | direct host of the environment's Neon project |
| `PB_DB_NAME` | `partitelle` |
| `PB_DB_USER` | `partitelle_owner` |
| `PB_DB_PASSWORD` | role password from the Neon console |
| `PB_DB_PORT` | `5432` |
| `PB_DB_SCHEMA` | `prod` / `staging` |

Tables are created by the yoyo migrations at startup (start command `python3 -m db.migrate && python3 main.py`).

## Applying env var changes on Render

"Restart service" does NOT pick up changed env group values: a deploy does.

- Staging: Manual Deploy, "Deploy latest commit" (staging always runs `main`).
- Prod: deploy only the commit of the latest release. "Deploy latest commit" is safe only if `main` HEAD is the latest release tag; otherwise use Manual Deploy, "Deploy a specific commit" with the commit of the latest tag (`git tag --sort=-creatordate | head -1`). Never deploy unreleased code.

The deploy logs show `Applying to schema '<schema>': [...]` then `Migrations applied`.

## Stats tracker

The `partitelle-bot-stats-tracker` repo reads prod through its GitHub Actions secrets `PB_DB_HOST`, `PB_DB_NAME`, `PB_DB_USER`, `PB_DB_PASSWORD` (and `PB_DB_SCHEMA=prod` if present). Update them when the host or password changes.

## Manual export and restore

There are no scheduled backups and Neon Free keeps only a short restore window, so export before risky changes. Keep dumps local and private (personal data), never commit them. Export only the data table, never the `_yoyo_*` tables.

```bash
docker run --rm postgres:17 pg_dump --data-only --table=prod.all_players "<direct connection string>" > prod-data.sql
docker run --rm -i -v "$PWD":/dump postgres:17 psql "<direct connection string>" -f /dump/prod-data.sql
```

A DBeaver "SQL" export starts with `DROP TABLE`/`CREATE TABLE`: strip them and keep only the `INSERT` statements, the table must come from the migrations.

## Testing a migration on real data

1. In the prod Neon project, create a temporary branch of the default branch.
2. Run the migrations locally against it:

   ```bash
   PB_DB_HOST=<branch host> PB_DB_NAME=partitelle PB_DB_USER=partitelle_owner \
   PB_DB_PASSWORD=<password> PB_DB_PORT=5432 PB_DB_SCHEMA=prod \
   uv run python -m db.migrate
   ```

3. Check the result, then delete the branch.

## Troubleshooting

- Tables not visible in the Neon console: select the `prod`/`staging` schema, the default view shows `public`.
- `pg_dump: error: aborting because of server version mismatch`: the local client is older than the server. Use the `postgres:17` Docker image.
- Migrations fail at start: the bot does not start (the start command uses `&&`). Check the deploy logs for the failing migration.
- Changed env vars have no effect: a restart is not enough, deploy (see above).
