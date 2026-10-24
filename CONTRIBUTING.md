# Contributing

Hello everybody! 💪

Any contribution to this project is appreciated and welcomed 😎
Just make sure that you follow these simple rules:

- Please, name your branch like: `feat/...` | `fix/...` | `chore/...` [in brief, use the correct prefix to indicate if it is a new feature, some fix or a version upgrade]
- Open a new PR and let's see if what you did works on [PartitelleBotTest](https://t.me/PartitelleTestBot) [as a best practice, the PR title should be like: `feat: ...` | `fix: ...` | `chore: ...`]
- If it works, I bring your contribution to [PartitelleBot](https://t.me/PartitelleBot)

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
