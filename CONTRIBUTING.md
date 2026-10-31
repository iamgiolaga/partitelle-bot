# Contributing

Hello everybody! 💪

Any contribution to this project is appreciated and welcomed 😎
Just make sure that you follow these simple rules:

- Please, name your branch like: `feat/...` | `fix/...` | `chore/...` [in brief, use the correct prefix to indicate if it is a new feature, some fix or a version upgrade]
- Open a new PR (the title must follow Conventional Commits: `feat: ...` | `fix: ...` | `chore: ...` | `doc: ...` | `test: ...`, it is checked by CI). The PR runs tests and lint; once merged, it is deployed to [PartitelleBotTest](https://t.me/PartitelleTestBot)
- If it works, I release it to [PartitelleBot](https://t.me/PartitelleBot) (see below)

See this [PR example](https://github.com/iamgiolaga/partitelle-bot/pull/20)

Best,
Giovanni

## Init the environment

This project uses [uv](https://docs.astral.sh/uv/) to manage Python and dependencies. After [installing uv](https://docs.astral.sh/uv/getting-started/installation/), run:

```bash
uv sync
```

This installs the python version specified in the `.python-version` file and all the dependencies (including the dev ones) in a local `.venv`.

If you change the dependencies in `pyproject.toml`, run `uv lock` and regenerate `requirements.txt` (used by Render):

```bash
uv export --no-dev --no-hashes --format requirements-txt -o requirements.txt
```

Code is formatted and linted with [ruff](https://docs.astral.sh/ruff/) (`ruff format` replaces black); CI runs both checks:

```bash
uv run ruff format .   # format
uv run ruff check .    # lint
```

Types are checked with [mypy](https://mypy.readthedocs.io/) (`uv run mypy`, also run by CI): `domain`, `db/connection.py` and `db/repository.py` are checked strictly, the rest of the code is not checked yet.
To bring a module under checking, fully annotate it and add it to `files` and to the strict override in the `[tool.mypy]` section of `pyproject.toml`.

Create a `.env` file and fill it with the correct values. You can use the `default.env` file as a template.

## Database migrations

The database structure is managed with [yoyo-migrations](https://ollycope.com/software/yoyo/latest/). Each environment (`staging`, `prod`) is a Postgres schema of the same database, selected by `PB_DB_SCHEMA`, with its own migration history (`<schema>._yoyo_migration`).

To change the structure, add a file `migrations/000N_<name>.sql` (next number, plain SQL, unqualified table names) starting with `-- depends: 000M_<previous name>`. Then apply it locally:

```bash
uv run --env-file .env python -m db.migrate
```

Rules:

- never edit a migration that has already been applied/merged: add a new one
- staging and prod migrate at their own deploys, so a migration must be backward compatible with the code currently deployed in the other environment (e.g. add nullable columns, do not drop or rename columns in the same release)
- `PB_DB_SCHEMA` is mandatory: the bot and `db.migrate` refuse to start without it
- the Neon database setup, env vars and backups are described in [docs/neon-db.md](docs/neon-db.md)

On Render, the start command of both services must be:

```bash
python -m db.migrate && python main.py
```

## Run the tests

To run the tests, run the following command:

```bash
uv run pytest
```

## Run the bot

To run the bot, run the following command:

```bash
uv run python main.py
```

If you're running the bot locally (ENV = local), the bot will start polling messages from Telegram.

If you're running the bot on other environments (ENV != local), the bot will start a webhook listener instead: it registers `$PB_URL/telegram` with Telegram at startup (`setWebhook`) and only accepts calls carrying the secret token, `PB_WEBHOOK_SECRET` if set (optional) or a value derived from the bot token otherwise. The bot token is never part of the URL.

The bot uses the async API of python-telegram-bot (handlers are `async def` and await every bot call). The database layer is still synchronous (psycopg pool), which is fine for the current traffic.

This is useful to test the bot on a local environment before pushing the changes to the remote server.

## Dependencies

[Dependabot](.github/dependabot.yml) checks `uv` and GitHub Actions dependencies every Monday. Patch and minor updates are grouped in one PR and auto-merged once CI is green (they only reach staging; prod follows with the weekly `Promote to prod` run, after at least 24 hours on staging). Major updates get their own PR and are reviewed manually. Dependabot does not touch `requirements.txt`, so the workflow regenerates it on every Dependabot PR (majors included) and CI fails if it is out of sync with `uv.lock`. Auto-merge needs the `AUTOMERGE_TOKEN` Dependabot secret (see the one-time setup below).

## Release & deploy flow

1. Open a PR with a Conventional Commits title; CI runs `unit-test` and `linter`.
2. Optional: add the `deploy-partitellebot-test` label to try the PR on PartitelleBotTest (staging) before merging. Once tests and lint pass, CI points the test service at the PR branch and deploys its head commit (and redeploys on every new push while the label is present). The test service is shared, so if two PRs are labeled the last deploy wins. Fork PRs are not deployed.
3. Squash-merge to `main`: after tests and lint pass, CI deploys that commit to staging (this also moves staging back to `main`).
4. Prod is promoted automatically every Thursday at 07:00 UTC, as long as the latest `main` commit has been on staging for at least 24 hours (otherwise that run is skipped); failures arrive as the usual failed-workflow email. You can also promote at any time, with no soak time: Actions > "Promote to prod" > Run workflow, or from the CLI:

   ```bash
   gh workflow run promote.yml                    # compute the version from commit types
   gh workflow run promote.yml -f dry_run=true    # only show version and release notes
   gh workflow run promote.yml -f version=2.0.0   # override the version
   ```

What "Promote to prod" does:

- Waits (up to 30 minutes) for any CI run in progress on `main`, so it can be pressed right after a merge.
- Scheduled runs only: skips cleanly if the latest `main` commit is less than 24 hours old (manual runs ignore this).
- Reads the commit live on staging from the Render API and fails if it is not on `main` (e.g. staging still runs a labeled PR branch: merge it, or redeploy `main` to staging), if its CI run on `main` is not green, or if it is not the latest `main` commit (the CI of a newer commit failed and staging stayed behind).
- Computes the next version with [git-cliff](https://git-cliff.org) (`cliff.toml`) from the Conventional Commits since the latest tag: `!`/`BREAKING CHANGE` = major, `feat` = minor, anything else = patch. Tags have no `v` prefix. An explicit `version` must be greater than the latest tag. If staging already runs the latest tag it stops with "nothing to promote".
- Smoke checks staging before deploying: its public URL must answer with an HTTP status below 500 (retried for up to 3 minutes, the free instance may be waking up), otherwise it fails and prod is untouched.
- On scheduled runs, re-enables itself through the API first, so GitHub never disables the schedule after 60 days without repo activity.
- Deploys that exact commit to PartitelleBot (prod) and, only if the deploy succeeded, creates the tag and the GitHub release (notes generated by git-cliff). Re-running after a partial failure is safe.
- The version lives only in git tags (`pyproject.toml` has a placeholder), and release notes live in GitHub Releases.

Deploys call the Render API with an explicit commit SHA (`.github/scripts/render-deploy.sh`).

### One-time setup (owner)

- Render: turn OFF auto-deploy on both services and set `PYTHON_VERSION=3.12.12` (it must match `.python-version`).
- Secrets: `RENDER_SERVICE_ID`, `RENDER_API_KEY`, `RENDER_TEST_SERVICE_ID`, `RENDER_TEST_API_KEY`.
- Secret `AUTOMERGE_TOKEN` (Dependabot secret, not an Actions one): fine-grained PAT limited to this repo with `Contents`, `Pull requests` and `Workflows` read and write (`Workflows` is needed to merge GitHub Actions bumps and push to their branches), no expiration, used by `dependabot-auto-merge.yml`. It is a PAT because merges made with `GITHUB_TOKEN` do not trigger the `push` workflow on `main`, so staging would not be deployed.
