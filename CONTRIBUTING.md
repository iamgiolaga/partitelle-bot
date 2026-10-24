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
- `PB_DB_SCHEMA` unset or `public` is the legacy layout: migrations are skipped
- the Render database setup, the one-time move to schemas and the monthly recreation are described in [docs/render-db-recreation.md](docs/render-db-recreation.md)

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

If you're running the bot on other environments (ENV != local), the bot will start a webhook listener instead.

This is useful to test the bot on a local environment before pushing the changes to the remote server.

## Release & deploy flow

1. Open a PR with a Conventional Commits title; CI runs `unit-test` and `linter`.
2. Squash-merge to `main`: after tests and lint pass, that commit is deployed to PartitelleBotTest (staging).
3. [release-please](https://github.com/googleapis/release-please) keeps a release PR open that bumps the version in `pyproject.toml` and updates `CHANGELOG.md` (`feat` = minor, `fix`/`perf` = patch, `!` or `BREAKING CHANGE` = major). The CI `release-please` job then runs `uv lock` on the release PR branch and pushes a `chore: update uv.lock for release` commit, so `uv.lock` stays in sync automatically.
4. Merging the release PR creates the tag (no `v` prefix) and the GitHub release, then deploys that exact commit to PartitelleBot (prod).
5. Emergency: create the release by hand, then run the `CI` workflow manually (Actions > CI > Run workflow) selecting the tag/branch to deploy to prod.

Deploys call the Render API with an explicit commit SHA (`.github/scripts/render-deploy.sh`).

To try a PR on PartitelleBotTest before merging, add the `deploy-partitellebot-test` label: once tests and lint pass, CI points the test service at the PR branch and deploys its head commit (and redeploys on every new push while the label is present). The test service is shared, so if two PRs are labeled the last deploy wins; it goes back to `main` on the next merge. Fork PRs are not deployed.

### One-time setup (owner)

- Render: turn OFF auto-deploy on both services and set `PYTHON_VERSION=3.11.9`.
- GitHub: Settings > Actions > General > enable "Allow GitHub Actions to create and approve pull requests" (needed by release-please).
- Release PRs opened with `GITHUB_TOKEN` do not trigger workflows, so the required `unit-test` check will not run on them. Either merge them as an admin (bypass), or create a fine-grained PAT (contents + pull requests: read/write) and store it as the `RELEASE_PLEASE_TOKEN` secret; it is used automatically when present.
- Secrets: `RENDER_SERVICE_ID`, `RENDER_API_KEY`, `RENDER_TEST_SERVICE_ID`, `RENDER_TEST_API_KEY`.
