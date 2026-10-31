# CLAUDE.md

Telegram bot (Python 3.12, uv) that organizes casual team games among friends. Runs on Render with Postgres.

## Read first
- [README.md](README.md) for what the bot does.
- [CONTRIBUTING.md](CONTRIBUTING.md) for setup, migrations, the release flow and the Dependabot policy.
- [docs/neon-db.md](docs/neon-db.md) for the database setup.

## Rules
- Keep `domain/` free of Telegram and database code: it must not import `telegram`, `psycopg` or `db`. (Checked today: it holds; `domain/` only imports the standard library, `dateutil` and `utils.constants`.)
- Small, focused PRs. New behavior comes with feature tests (`test/features`) and strict assertions on the exact outcome, not just "does not raise".
- Before opening a PR run what CI runs (the coverage gate is 97%):
  - `uv sync --locked`
  - `uv run pytest test --cov=callbacks --cov=behaviours --cov=jobs --cov=db --cov=utils --cov=handlers --cov=domain --cov-fail-under=97`
  - `uv run ruff check`, `uv run ruff format --check` and `uv run mypy`
  - `uv lock --check`, and regenerate `requirements.txt` when dependencies change (command in CONTRIBUTING)
- Branches are `feat/...`, `fix/...` or `chore/...`. PR titles follow Conventional Commits (`feat`, `fix`, `chore`, `doc`, `test`); CI checks them. History is squash-merged with the PR number.
- Migrations: never edit an applied one, add a new one; keep them backward compatible (see CONTRIBUTING).

## Gates
- Never push to `main`; open a PR.
- A push to `main` auto-deploys staging. The prod promote (`promote.yml`) is manual (`workflow_dispatch`).
- Merging, deploying and running the prod promote need a maintainer's explicit OK.

Company context: if you have access to the private repo `partitelle/hq` (usually cloned at `../partitelle-hq`), read its CLAUDE.md for decisions, priorities and approval rules. This repo must stay self-contained without it.
