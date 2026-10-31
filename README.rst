.. image:: .github/img/logo.png
   :width: 160px
   :align: center
   :alt: PartitelleBot logo

====================
PartitelleBot
====================

Telegram bot that organizes amateur football matches among friends: who is in, who is maybe, and the teams.

.. image:: https://img.shields.io/badge/Telegram-PartitelleBot-blue.svg?logo=telegram
   :align: center
   :target: https://t.me/PartitelleBot
   :alt: PartitelleBot

What it is
==========

PartitelleBot keeps the participant list of the weekly match in a Telegram group and updates a single summary message as people join or drop out.
When the list is full it splits the players into two random teams, and after the match it reminds the group to pay the pitch.
The bot talks Italian; this README is in English.

It is a Python 3.12 project built on the async API of `python-telegram-bot <https://github.com/python-telegram-bot/python-telegram-bot>`_ (v22), with PostgreSQL for storage, both hosted on `Render <https://dashboard.render.com>`_.

How to use it in a group
========================

1. Add `@PartitelleBot <https://t.me/PartitelleBot>`_ to the group. Giving it administrator rights lets it pin its messages.
2. Send ``/start`` to create the match. By default it is the next Wednesday at 20:00 (today, if it is a Wednesday and 20:00 has not passed yet), with 10 players. Change it with ``/setday``, ``/settime`` and ``/setnumber``.
3. Everybody writes plain chat keywords (see below) to join. The bot prints the summary the first time and then edits it in place; ``/participants`` shows it again on demand.
4. Once the confirmed players reach the target, the bot announces it and you can run ``/teams`` to get a black and a white team.
5. Teams can be adjusted with ``scambia <name 1> con <name 2>``. Removing a player or marking one as maybe revokes the teams (the bot says so); ``/teams`` generates them again.
6. Two hours after the match starts, the bot asks the group whether everybody paid, and pins the message if it can.

The summary looks like this (the pitch and the description are editable)::

    GIORNO: Mercoledì 04/11/2026 | 20:00

    1. Anna ✅
    2. Marco ❓
    3. ❌
    ...

    <description>

    CAMPO:
    <pitch>

``✅`` is confirmed, ``❓`` is maybe, ``❌`` is a free slot.

Chat keywords
-------------

Keywords are plain messages, not commands. The message must start exactly with the keyword, and names are matched ignoring case.
``aggiungi``, ``proponi`` accept several comma-separated names (``aggiungi luca, sara``). The names are free text: they do not have to be Telegram users.

=================================== ===================================================================================
Message                             Effect
=================================== ===================================================================================
``aggiungimi``                      add yourself, or confirm yourself if you were maybe
``aggiungi <name>``                 add someone, or confirm them if they were maybe
``proponimi``                       add yourself as maybe
``proponi <name>``                  add someone as maybe
``toglimi``                         remove yourself, whether confirmed or maybe
``togli <name>``                    remove one person, whether confirmed or maybe
``scambia <name 1> con <name 2>``   swap two players of different teams (needs teams from ``/teams``)
=================================== ===================================================================================

Commands
========

``/setday`` and ``/settime`` read a human date or time and refuse anything they cannot understand.

========================== ================================================================================================
Command                    Description
========================== ================================================================================================
``/start``                 create the match of the chat (does nothing if one is already active)
``/setnumber <n>``         number of players, up to 40; teams need an even number. Revokes existing teams
``/setday <date>``         day of the match, day first, e.g. ``/setday 25/10/2026``
``/settime <time>``        time of the match, e.g. ``/settime 21:30``, ``/settime 21.30`` or ``/settime 20``
``/setdescription <text>`` text shown under the list; Telegram markdown is allowed
``/setpitch <name>``       pitch shown at the bottom of the summary
``/participants``          show the summary of the current match
``/teams``                 generate the teams once the target is reached, or show the existing ones
``/stop``                  stop the current match; it is kept as history and ``/start`` can create a new one
``/help``                  list keywords and commands
========================== ================================================================================================

Development
===========

Setup, workflow and conventions are in `CONTRIBUTING.md <https://github.com/partitelle/partitelle-bot/blob/main/CONTRIBUTING.md>`_.

Prerequisites: `uv <https://docs.astral.sh/uv/>`_ and `Docker <https://www.docker.com/>`_.

1. create your own bot with `BotFather <https://t.me/BotFather>`_ and copy its token
2. ``cp default.env .env`` and set ``PB_TG_TOKEN`` to your token
3. ``docker compose up -d`` starts a local PostgreSQL
4. ``uv sync`` installs the dependencies
5. ``uv run --env-file .env python -m db.migrate`` creates the ``PB_DB_SCHEMA`` schema and applies the migrations in ``migrations/``
6. ``uv run --env-file .env python main.py`` starts the bot (with ``ENV=local`` it uses polling instead of a webhook)
7. ``uv run pytest`` runs the tests

The ``.env`` file is not loaded automatically by the code: pass it with ``uv run --env-file .env`` as above (or export the variables in your shell).
Use ``docker compose down -v`` to also drop the local data.

=================== ======================================================================
Variable            Meaning
=================== ======================================================================
ENV                 ``local`` runs the bot in polling mode, any other value uses a webhook
PB_TG_TOKEN         Telegram bot token
PB_URL              public URL of the hosting, used for the webhook (not needed locally)
PB_WEBHOOK_SECRET   optional secret Telegram sends with every webhook call (``[A-Za-z0-9_-]``, 1-256 chars); when unset it is derived from ``PB_TG_TOKEN``
PB_DB_SCHEMA        PostgreSQL schema of the environment: ``prod`` or ``staging`` (mandatory: the bot does not start without it)
PB_DB_HOST          PostgreSQL host
PB_DB_NAME          PostgreSQL database name
PB_DB_USER          PostgreSQL user
PB_DB_PASSWORD      PostgreSQL password
PB_DB_PORT          PostgreSQL port (also the host port published by docker compose)
=================== ======================================================================

Sponsorships
============

Nothing mandatory, just do it if you feel like offering a coffee: tap the Sponsor button at the top, or click `here <https://paypal.me/GiovanniL891?country.x=IT&locale.x=it_IT>`_.

License
=======

Released under the GNU General Public License v3.0, see `LICENSE <LICENSE>`__.
