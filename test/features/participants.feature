Feature: Managing the participants
  Free-text messages (no slash) add, propose, remove and swap participants of the match of the chat:
  aggiungimi / aggiungi <nome>, proponimi / proponi <nome>, toglimi / togli <nome>, scambia <a> con <b>.
  A proposed player is "in forse" (maybe present). Messages are case-insensitive and the bot
  answers with a short remark, then the updated summary (edited in place if it already exists).

  Background:
    Given a group chat "Calcetto"
    And the user "@mario"
    And today is "2026-10-21 18:00"
    And the text "default description" is:
      """
      5 goal di scarto e le squadre si _potrebbero_ cambiare 
      6 goal di scarto e le squadre si *devono* cambiare 
      (ditelo a chiunque invitate) 
      *PORTARE UNA MAGLIA BIANCA E UNA COLORATA*

      """
    And the text "header" is:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00
      """
    And the text "footer" is:
      """
      {default description}

      *CAMPO*: 
      Usa il comando /setpitch <campo> per inserire la struttura sportiva dove giocherete.
      """
    And the text "no match" is:
      """
      Prima di iniziare con le danze, avvia una partita, per farlo usa /start
      """
    And the text "kickoff" is:
      """
      🚀 *SI GIOCA* 🚀 facciamo le squadre? /teams 😎
      """
    And the text "teams revoked" is:
      """
      *SQUADRE ANNULLATE*
      """

  # ---- before /start ---------------------------------------------------------------------------

  Scenario Outline: "<message>" before /start is refused and does not create a match
    When "@mario" sends "<message>"
    Then the bot should send the text "no match"
    And the bot should send nothing else
    And there should be no match for this chat

    Examples:
      | message                |
      | aggiungimi             |
      | aggiungi luca          |
      | proponimi              |
      | proponi luca           |
      | toglimi                |
      | togli luca             |
      | scambia luca con anna  |

  Scenario: Messages that are not participant intents are ignored
    Given a match was started
    When "@mario" sends "ciao a tutti"
    And "@mario" sends "ma che fine ha fatto luca?"
    Then the bot should send nothing else
    And the match should have:
      | field   | value  |
      | players | (none) |

  # ---- aggiungimi ---------------------------------------------------------------------------------

  Scenario: aggiungimi adds the sender and posts a new pinned summary
    Given a match was started
    And the match target is 4
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Ok, @mario, ti aggiungo
      """
    And the bot should send:
      """
      {header}

      1. @mario ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value  |
      | players | @mario |

  Scenario: aggiungimi edits the existing summary in place and pins it again
    Given a match was started
    And the match target is 4
    And "@mario" had sent "/participants"
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Ok, @mario, ti aggiungo
      """
    And the bot should edit the summary to:
      """
      {header}

      1. @mario ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else

  Scenario: aggiungimi appends after the players already in the list
    Given a match was started
    And the match target is 4
    And the match has the players "@anna, luca"
    And the user "@carlo"
    When "@carlo" sends "aggiungimi"
    Then the bot should send:
      """
      Ok, @carlo, ti aggiungo
      """
    And the bot should send:
      """
      {header}

      1. @anna ✅
      2. luca ✅
      3. @carlo ✅
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value                |
      | players | @anna, luca, @carlo  |

  Scenario: aggiungimi twice does not duplicate the sender
    Given a match was started
    And the match target is 4
    And the match has the players "@mario"
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Ma @mario, sei già nella lista
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value  |
      | players | @mario |

  Scenario: aggiungimi confirms a player who was only maybe present
    Given a match was started
    And the match target is 4
    And the match has the players "@anna, @mario (maybe)"
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Ok, @mario, ti confermo
      """
    And the bot should send:
      """
      {header}

      1. @anna ✅
      2. @mario ✅
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value         |
      | players | @anna, @mario |

  Scenario: Intents are case-insensitive and usernames are lowercased
    Given a match was started
    And the match target is 4
    And the user "@MarioRossi"
    When "@MarioRossi" sends "AGGIUNGIMI"
    Then the bot should send:
      """
      Ok, @mariorossi, ti aggiungo
      """
    And the bot should send:
      """
      {header}

      1. @mariorossi ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  # ---- users without username ---------------------------------------------------------------------

  @known-bug
  Scenario Outline: <message> from a user without username crashes the handler
    Given a match was started
    And a user named "Luca" without username
    And the bot is expected to crash on the next message
    When "Luca" sends "<message>"
    Then the bot should fail with "AttributeError"
    And the bot should send nothing else
    And the match should have:
      | field   | value  |
      | players | (none) |

    Examples:
      | message    |
      | aggiungimi |
      | proponimi  |
      | toglimi    |

  Scenario: aggiungi <nome> works for a user without username
    Given a match was started
    And the match target is 4
    And a user named "Luca" without username
    When "Luca" sends "aggiungi luca"
    Then the bot should send:
      """
      Ok, aggiungo luca
      """
    And the bot should send:
      """
      {header}

      1. luca ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  # ---- aggiungi <nome> ----------------------------------------------------------------------------

  Scenario: aggiungi <nome> adds the name lowercased
    Given a match was started
    And the match target is 4
    When "@mario" sends "Aggiungi Luca"
    Then the bot should send:
      """
      Ok, aggiungo luca
      """
    And the bot should send:
      """
      {header}

      1. luca ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value |
      | players | luca  |

  Scenario: aggiungi <nome> accepts a name with spaces and edits the existing summary
    Given a match was started
    And the match target is 4
    And "@mario" had sent "/participants"
    When "@mario" sends "aggiungi luca rossi"
    Then the bot should send:
      """
      Ok, aggiungo luca rossi
      """
    And the bot should edit the summary to:
      """
      {header}

      1. luca rossi ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else

  Scenario: aggiungi <nome> of a name already in the list does nothing
    Given a match was started
    And the match target is 4
    And the match has the players "luca"
    When "@mario" sends "aggiungi luca"
    Then the bot should send:
      """
      luca è già nella lista
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value |
      | players | luca  |

  Scenario: aggiungi <nome> confirms a maybe present name
    Given a match was started
    And the match target is 4
    And the match has the players "luca (maybe)"
    When "@mario" sends "aggiungi luca"
    Then the bot should send:
      """
      Ok, luca, ti confermo
      """
    And the bot should send:
      """
      {header}

      1. luca ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value |
      | players | luca  |

  Scenario: Markdown characters in names are escaped in the bot's texts
    Given a match was started
    And the match target is 4
    When "@mario" sends "aggiungi gian_luca"
    Then the bot should send:
      """
      Ok, aggiungo gian\_luca
      """
    And the bot should send:
      """
      {header}

      1. gian\_luca ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value     |
      | players | gian_luca |

  @known-bug
  Scenario: aggiungi a,b,c adds the whole text as one name, so the same list can be added twice
    Given a match was started
    And the match target is 4
    When "@mario" sends "aggiungi a,b,c"
    Then the bot should send:
      """
      Ok, aggiungo a,b,c
      """
    And the bot should send:
      """
      {header}

      1. a ✅
      2. b ✅
      3. c ✅
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    When "@mario" sends "aggiungi a,b,c"
    Then the bot should send:
      """
      Ok, aggiungo a,b,c
      """
    And the bot should edit the summary to:
      """
      {header}

      1. a ✅
      2. b ✅
      3. c ✅
      4. a ✅

      {footer}
      """
    And the bot should pin the summary
    And the bot should send the text "kickoff"
    And the bot should send nothing else
    And the match should have:
      | field   | value         |
      | players | a, b, c, a, b, c |

  @known-bug
  Scenario: aggiungi without a name adds an empty name and then every addition crashes
    Given a match was started
    And the match target is 4
    When "@mario" sends "aggiungi"
    Then the bot should send the quoted text "Ok, aggiungo "
    And the bot should send:
      """
      {header}

      1. ❌
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    Given the bot is expected to crash on the next message
    When "@mario" sends "aggiungimi"
    Then the bot should fail with "InvalidTextRepresentation"
    And the bot should send nothing else

  @known-bug
  Scenario: A chatty message starting with aggiungimi adds the following words as a name
    Given a match was started
    And the match target is 4
    When "@mario" sends "Aggiungimi pure"
    Then the bot should send:
      """
      Ok, aggiungo pure
      """
    And the bot should send:
      """
      {header}

      1. pure ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value |
      | players | pure  |

  @known-bug @issue-61
  Scenario: A /command written after aggiungi is accepted as a name
    Given a match was started
    And the match target is 4
    When "@mario" sends "aggiungi /start"
    Then the bot should send:
      """
      Ok, aggiungo /start
      """
    And the bot should send:
      """
      {header}

      1. /start ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value  |
      | players | /start |

  # ---- proponimi / proponi <nome> -----------------------------------------------------------------

  Scenario: proponimi adds the sender as maybe present
    Given a match was started
    And the match target is 4
    When "@mario" sends "proponimi"
    Then the bot should send:
      """
      Ok, @mario, ti propongo
      """
    And the bot should send:
      """
      {header}

      1. @mario ❓
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value          |
      | players | @mario (maybe) |

  Scenario: proponimi twice does not change anything
    Given a match was started
    And the match target is 4
    And the match has the players "@mario (maybe)"
    When "@mario" sends "proponimi"
    Then the bot should send:
      """
      Ma @mario, sei già in forse
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value          |
      | players | @mario (maybe) |

  Scenario: proponimi downgrades a confirmed player to maybe present
    Given a match was started
    And the match target is 4
    And the match has the players "@anna, @mario"
    And "@mario" had sent "/participants"
    When "@mario" sends "proponimi"
    Then the bot should send:
      """
      Ok, @mario, ti metto in forse
      """
    And the bot should edit the summary to:
      """
      {header}

      1. @anna ✅
      2. @mario ❓
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match should have:
      | field   | value                 |
      | players | @anna, @mario (maybe) |

  Scenario: proponimi of a confirmed player revokes the teams
    Given a match was started
    And the match target is 4
    And the match has the players "@anna, @mario, luca, sara"
    And the match has the black team "@anna, luca" and the white team "@mario, sara"
    When "@mario" sends "proponimi"
    Then the bot should send:
      """
      Ok, @mario, ti metto in forse
      """
    And the bot should send the text "teams revoked"
    And the bot should send:
      """
      {header}

      1. @anna ✅
      2. luca ✅
      3. sara ✅
      4. @mario ❓

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value                        |
      | players | @anna, luca, sara, @mario (maybe) |
      | teams   | (none)                       |

  Scenario: proponi <nome> adds the name as maybe present
    Given a match was started
    And the match target is 4
    When "@mario" sends "Proponi Luca"
    Then the bot should send:
      """
      Ok, propongo luca
      """
    And the bot should send:
      """
      {header}

      1. luca ❓
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value        |
      | players | luca (maybe) |

  Scenario: proponi <nome> of a name already maybe present does nothing
    Given a match was started
    And the match target is 4
    And the match has the players "luca (maybe)"
    When "@mario" sends "proponi luca"
    Then the bot should send:
      """
      luca è già nella lista
      """
    And the bot should send nothing else

  Scenario: proponi <nome> downgrades a confirmed name and revokes the teams
    Given a match was started
    And the match target is 4
    And the match has the players "anna, bea, carlo, dino"
    And the match has the black team "anna, bea" and the white team "carlo, dino"
    When "@mario" sends "proponi carlo"
    Then the bot should send:
      """
      Va bene, metto in forse carlo
      """
    And the bot should send the text "teams revoked"
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. bea ✅
      3. dino ✅
      4. carlo ❓

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value                      |
      | players | anna, bea, dino, carlo (maybe) |
      | teams   | (none)                     |

  Scenario: A maybe present proposal does not count as a confirmed player for the kickoff
    Given a match was started
    And the match target is 2
    And the match has the players "anna"
    When "@mario" sends "proponimi"
    Then the bot should send:
      """
      Ok, @mario, ti propongo
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. @mario ❓

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  @known-bug @issue-78
  Scenario: proponi a,b,c confirms all but the last name
    Given a match was started
    And the match target is 4
    When "@mario" sends "proponi a,b,c"
    Then the bot should send:
      """
      Ok, propongo a,b,c
      """
    And the bot should send:
      """
      {header}

      1. a ✅
      2. b ✅
      3. c ❓
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value        |
      | players | a, b, c (maybe) |

  @known-bug @issue-61
  Scenario: A /command written after proponi is accepted as a name
    Given a match was started
    And the match target is 4
    When "@mario" sends "proponi /stop"
    Then the bot should send:
      """
      Ok, propongo /stop
      """
    And the bot should send:
      """
      {header}

      1. /stop ❓
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  @known-bug
  Scenario: proponi without a name proposes an empty name
    Given a match was started
    And the match target is 4
    When "@mario" sends "proponi"
    Then the bot should send the quoted text "Ok, propongo "
    And the bot should send:
      """
      {header}

      1.  ❓
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  # ---- toglimi / togli <nome> ---------------------------------------------------------------------

  Scenario: toglimi removes a confirmed sender and empties the list
    Given a match was started
    And the match target is 4
    And the match has the players "@mario"
    When "@mario" sends "toglimi"
    Then the bot should send:
      """
      Mamma mia... che paccaro
      """
    And the bot should send:
      """
      {header}

      1. ❌
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value  |
      | players | (none) |

  Scenario: toglimi removes a maybe present sender and keeps the others in order
    Given a match was started
    And the match target is 4
    And the match has the players "@anna, @mario (maybe), luca"
    And "@mario" had sent "/participants"
    When "@mario" sends "toglimi"
    Then the bot should send:
      """
      Peccato, un po' ci avevo sperato
      """
    And the bot should edit the summary to:
      """
      {header}

      1. @anna ✅
      2. luca ✅
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match should have:
      | field   | value      |
      | players | @anna, luca |

  Scenario: toglimi when not in the list does nothing
    Given a match was started
    And the match target is 4
    And the match has the players "@anna"
    When "@mario" sends "toglimi"
    Then the bot should send:
      """
      Non eri in lista neanche prima
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value |
      | players | @anna |

  Scenario: toglimi on an empty list does nothing
    Given a match was started
    When "@mario" sends "toglimi"
    Then the bot should send:
      """
      Non eri in lista neanche prima
      """
    And the bot should send nothing else

  Scenario: toglimi revokes the teams
    Given a match was started
    And the match target is 4
    And the match has the players "@anna, @mario, luca, sara"
    And the match has the black team "@anna, luca" and the white team "@mario, sara"
    When "@mario" sends "toglimi"
    Then the bot should send:
      """
      Mamma mia... che paccaro
      """
    And the bot should send the text "teams revoked"
    And the bot should send:
      """
      {header}

      1. @anna ✅
      2. luca ✅
      3. sara ✅
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value             |
      | players | @anna, luca, sara |
      | teams   | (none)            |

  Scenario: togli <nome> removes a confirmed name
    Given a match was started
    And the match target is 4
    And the match has the players "anna, luca"
    When "@mario" sends "Togli Luca"
    Then the bot should send:
      """
      Che vergogna, luca
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value |
      | players | anna  |

  Scenario: togli <nome> removes a maybe present name
    Given a match was started
    And the match target is 4
    And the match has the players "anna, luca (maybe)"
    When "@mario" sends "togli luca"
    Then the bot should send:
      """
      Davvero? Ma luca, ne sei proprio sicuro?
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  Scenario: togli <nome> of an unknown name does nothing
    Given a match was started
    And the match target is 4
    And the match has the players "anna"
    When "@mario" sends "togli luca"
    Then the bot should send:
      """
      luca non è nella lista. Chi dovrei togliere?
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value |
      | players | anna  |

  Scenario: togli <nome> revokes the teams
    Given a match was started
    And the match target is 4
    And the match has the players "anna, bea, carlo, dino"
    And the match has the black team "anna, bea" and the white team "carlo, dino"
    When "@mario" sends "togli bea"
    Then the bot should send:
      """
      Che vergogna, bea
      """
    And the bot should send the text "teams revoked"
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. carlo ✅
      3. dino ✅
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field | value  |
      | teams | (none) |

  @known-bug
  Scenario: togli without a name asks whom to remove with a broken sentence
    Given a match was started
    And the match has the players "anna"
    When "@mario" sends "togli"
    Then the bot should send the quoted text " non è nella lista. Chi dovrei togliere?"
    And the bot should send nothing else

  @known-bug
  Scenario: A chatty message starting with toglimi is read as togli <nome>
    Given a match was started
    And the match has the players "anna"
    When "@mario" sends "toglimi grazie"
    Then the bot should send:
      """
      grazie non è nella lista. Chi dovrei togliere?
      """
    And the bot should send nothing else

  @known-bug @issue-61
  Scenario: A /command written after togli is accepted as a name
    Given a match was started
    And the match target is 4
    And the match has the players "/start"
    When "@mario" sends "togli /start"
    Then the bot should send:
      """
      Che vergogna, /start
      """
    And the bot should send:
      """
      {header}

      1. ❌
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value  |
      | players | (none) |

  # ---- scambia <a> con <b> ------------------------------------------------------------------------

  Scenario: scambia without teams asks to form them first
    Given a match was started
    And the match has the players "anna, bea"
    When "@mario" sends "scambia anna con bea"
    Then the bot should send:
      """
      Per usare questa funzionalità devi prima formare delle squadre con /teams
      """
    And the bot should send nothing else

  Scenario: scambia swaps two players of different teams
    Given a match was started
    And the match target is 4
    And the match has the players "anna, bea, carlo, dino"
    And the match has the black team "anna, bea" and the white team "carlo, dino"
    When "@mario" sends "Scambia Anna con Carlo"
    Then the bot should send:
      """
      Perfetto, ho scambiato anna con carlo
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                                |
      | teams | black: carlo, bea \| white: anna, dino |

  Scenario: scambia works in both directions
    Given a match was started
    And the match target is 4
    And the match has the players "anna, bea, carlo, dino"
    And the match has the black team "anna, bea" and the white team "carlo, dino"
    When "@mario" sends "scambia dino con bea"
    Then the bot should send:
      """
      Perfetto, ho scambiato dino con bea
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                                |
      | teams | black: anna, dino \| white: carlo, bea |

  Scenario: scambia refuses two players of the same team
    Given a match was started
    And the match target is 4
    And the match has the players "anna, bea, carlo, dino"
    And the match has the black team "anna, bea" and the white team "carlo, dino"
    When "@mario" sends "scambia anna con bea"
    Then the bot should send:
      """
      anna e bea sono nella stessa squadra!
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                                |
      | teams | black: anna, bea \| white: carlo, dino |

  Scenario: scambia names the first unknown player
    Given a match was started
    And the match target is 4
    And the match has the players "anna, bea, carlo, dino"
    And the match has the black team "anna, bea" and the white team "carlo, dino"
    When "@mario" sends "scambia zeno con carlo"
    Then the bot should send:
      """
      zeno non c'è
      """
    And the bot should send nothing else

  Scenario: scambia names the second unknown player
    Given a match was started
    And the match target is 4
    And the match has the players "anna, bea, carlo, dino"
    And the match has the black team "anna, bea" and the white team "carlo, dino"
    When "@mario" sends "scambia anna con zeno"
    Then the bot should send:
      """
      zeno non c'è
      """
    And the bot should send nothing else

  Scenario: scambia does not see a maybe present player
    Given a match was started
    And the match target is 4
    And the match has the players "anna, bea, carlo, dino, enzo (maybe)"
    And the match has the black team "anna, bea" and the white team "carlo, dino"
    When "@mario" sends "scambia anna con enzo"
    Then the bot should send:
      """
      enzo non c'è
      """
    And the bot should send nothing else

  @known-bug
  Scenario: scambia with a player who is in the list but not in the teams drops the other player
    Given a match was started
    And the match target is 6
    And the match has the players "anna, bea, carlo, dino, enzo"
    And the match has the black team "anna, bea" and the white team "carlo, dino"
    When "@mario" sends "scambia anna con enzo"
    Then the bot should send:
      """
      Perfetto, ho scambiato anna con enzo
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                               |
      | teams | black: enzo, bea \| white: carlo, dino |

  @known-bug
  Scenario Outline: scambia without " con" crashes the handler
    Given a match was started
    And the bot is expected to crash on the next message
    When "@mario" sends "<message>"
    Then the bot should fail with "ValueError"
    And the bot should send nothing else

    Examples:
      | message      |
      | scambia      |
      | scambia anna |

  # ---- the target of the match ---------------------------------------------------------------------

  Scenario: Adding the last missing player kicks off the match
    Given a match was started
    And the match target is 2
    And the match has the players "anna"
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Ok, @mario, ti aggiungo
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. @mario ✅

      {footer}
      """
    And the bot should pin the summary
    And the bot should send the text "kickoff"
    And the bot should send nothing else

  Scenario: Confirming the last missing player kicks off the match
    Given a match was started
    And the match target is 2
    And the match has the players "anna, @mario (maybe)"
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Ok, @mario, ti confermo
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. @mario ✅

      {footer}
      """
    And the bot should pin the summary
    And the bot should send the text "kickoff"
    And the bot should send nothing else

  Scenario: aggiungi <nome> reaching the target kicks off the match and edits the summary
    Given a match was started
    And the match target is 2
    And the match has the players "anna"
    And "@mario" had sent "/participants"
    When "@mario" sends "aggiungi bea"
    Then the bot should send:
      """
      Ok, aggiungo bea
      """
    And the bot should edit the summary to:
      """
      {header}

      1. anna ✅
      2. bea ✅

      {footer}
      """
    And the bot should pin the summary
    And the bot should send the text "kickoff"
    And the bot should send nothing else

  Scenario: Confirming a maybe present name with aggiungi <nome> kicks off the match
    Given a match was started
    And the match target is 2
    And the match has the players "anna, bea (maybe)"
    When "@mario" sends "aggiungi bea"
    Then the bot should send:
      """
      Ok, bea, ti confermo
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. bea ✅

      {footer}
      """
    And the bot should pin the summary
    And the bot should send the text "kickoff"
    And the bot should send nothing else

  Scenario: Adding while the list is full is refused
    Given a match was started
    And the match target is 2
    And the match has the players "anna, bea"
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Siete già in 2
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value    |
      | players | anna, bea |

  Scenario Outline: <message> while the list is full is refused
    Given a match was started
    And the match target is 2
    And the match has the players "anna, bea"
    When "@mario" sends "<message>"
    Then the bot should send:
      """
      Siete già in 2
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value    |
      | players | anna, bea |

    Examples:
      | message       |
      | aggiungi luca |
      | proponimi     |
      | proponi luca  |

  Scenario: A confirmed player can still become maybe present while the list is full
    Given a match was started
    And the match target is 2
    And the match has the players "anna, @mario"
    When "@mario" sends "proponimi"
    Then the bot should send:
      """
      Ok, @mario, ti metto in forse
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. @mario ❓

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  @known-bug @issue-60
  Scenario: Siete già in N is said even when maybe present players fill the list
    Given a match was started
    And the match target is 2
    And the match has the players "anna, bea (maybe)"
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Siete già in 2
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value            |
      | players | anna, bea (maybe) |

  @known-bug
  Scenario: A target of 1 never kicks off the match
    Given a match was started
    And the match target is 1
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Ok, @mario, ti aggiungo
      """
    And the bot should send:
      """
      {header}

      1. @mario ✅

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  Scenario: Adding a player after the teams are formed keeps the teams
    Given a match was started
    And the match target is 6
    And the match has the players "anna, bea, carlo, dino"
    And the match has the black team "anna, bea" and the white team "carlo, dino"
    When "@mario" sends "aggiungi enzo"
    Then the bot should send:
      """
      Ok, aggiungo enzo
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. bea ✅
      3. carlo ✅
      4. dino ✅
      5. enzo ✅
      6. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field | value                                |
      | teams | black: anna, bea \| white: carlo, dino |

  # ---- /participants and the summary message -------------------------------------------------------

  Scenario: /participants shows the players, confirmed and maybe present
    Given a match was started
    And the match target is 4
    And the match has the players "anna, luca (maybe), @mario"
    When "@mario" sends "/participants"
    Then the bot should send:
      """
      {header}

      1. anna ✅
      2. luca ❓
      3. @mario ✅
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  Scenario: /participants posts a new summary that the next changes edit
    Given a match was started
    And the match target is 4
    When "@mario" sends "aggiungi anna"
    Then the bot should send:
      """
      Ok, aggiungo anna
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    When "@mario" sends "/participants"
    Then the bot should send:
      """
      {header}

      1. anna ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    When "@mario" sends "aggiungi bea"
    Then the bot should send:
      """
      Ok, aggiungo bea
      """
    And the bot should edit the summary to:
      """
      {header}

      1. anna ✅
      2. bea ✅
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else

  Scenario: Participants are kept per chat
    Given a group chat "Altra squadra"
    And a match was started
    And a group chat "Calcetto"
    And a match was started
    And the match target is 4
    When "@mario" sends "aggiungimi" in "Calcetto"
    Then the bot should send:
      """
      Ok, @mario, ti aggiungo
      """
    And the bot should send:
      """
      {header}

      1. @mario ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match of "Altra squadra" should have no players
