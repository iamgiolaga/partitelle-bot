Feature: Managing the participants
  Free-text messages (no slash) add, propose, remove and swap participants of the match of the chat:
  aggiungimi / aggiungi <nome>, proponimi / proponi <nome>, toglimi / togli <nome>, scambia <a> con <b>.
  A proposed player is "in forse" (maybe present). Messages are case-insensitive and the bot
  answers with a short remark, then the updated summary (edited in place if it already exists).

  Background:
    Given a group chat "Calcetto"
    And the user "@mario"
    And today is "2026-10-21 21:00"
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

  @issue-25
  Scenario Outline: An edited "<message>" is ignored
    Given a match was started
    And the match has the players "@mario, anna"
    When "@mario" edits a message into "<message>"
    Then the bot should send nothing else
    And the match should have:
      | field   | value        |
      | players | @mario, anna |

    Examples:
      | message               |
      | aggiungimi            |
      | proponimi             |
      | toglimi               |
      | aggiungi bea          |
      | togli anna            |
      | scambia anna con bea  |

  @issue-25
  Scenario Outline: <message> is ignored when the sender cannot be retrieved
    Given a match was started
    And the match target is 4
    And the match has the players "@mario, anna (maybe)"
    When "@mario" sends "<message>" and the bot cannot retrieve the sender
    Then the bot should send nothing else
    And the match should have:
      | field   | value                |
      | players | @mario, anna (maybe) |

    Examples:
      | message    |
      | aggiungimi |
      | proponimi  |
      | toglimi    |

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

  Scenario: aggiungimi stores a user without username by display name, without the @
    Given a match was started
    And the match target is 4
    And a user named "Luca" without username
    When "Luca" sends "aggiungimi"
    Then the bot should send:
      """
      Ok, Luca, ti aggiungo
      """
    And the bot should send:
      """
      {header}

      1. Luca ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value |
      | players | Luca  |

  Scenario: aggiungimi twice from a user without username does not duplicate the sender
    Given a match was started
    And the match target is 4
    And a user named "Luca" without username
    And the match has the players "Luca"
    When "Luca" sends "aggiungimi"
    Then the bot should send:
      """
      Ma Luca, sei già nella lista
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value |
      | players | Luca  |

  Scenario: A user with first and last name and no username is identified by the full name
    Given a match was started
    And the match target is 4
    And a user named "Luca" "Bianchi" without username
    When "Luca Bianchi" sends "aggiungimi"
    Then the bot should send:
      """
      Ok, Luca Bianchi, ti aggiungo
      """
    And the bot should send:
      """
      {header}

      1. Luca Bianchi ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value        |
      | players | Luca Bianchi |

  Scenario: proponimi and toglimi work for a user without username
    Given a match was started
    And the match target is 4
    And a user named "Luca" "Bianchi" without username
    When "Luca Bianchi" sends "proponimi"
    Then the bot should send:
      """
      Ok, Luca Bianchi, ti propongo
      """
    And the bot should send:
      """
      {header}

      1. Luca Bianchi ❓
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    When "Luca Bianchi" sends "toglimi"
    Then the bot should send:
      """
      Peccato, un po' ci avevo sperato
      """
    And the bot should edit the summary to:
      """
      {header}

      1. ❌
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match should have:
      | field   | value  |
      | players | (none) |

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

  Scenario: aggiungi <nome> sees a user without username added by display name as the same person
    Given a match was started
    And the match target is 4
    And a user named "Luca" without username
    And the match has the players "Luca"
    When "@mario" sends "aggiungi luca"
    Then the bot should send:
      """
      luca è già nella lista
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value |
      | players | Luca  |

  Scenario: aggiungimi confirms a user without username who was proposed with another case
    Given a match was started
    And the match target is 4
    And a user named "Luca" without username
    And the match has the players "anna, luca (maybe)"
    When "Luca" sends "aggiungimi"
    Then the bot should send:
      """
      Ok, Luca, ti confermo
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. luca ✅
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value      |
      | players | anna, luca |

  Scenario: togli <nome> removes a user without username who joined with the display name
    Given a match was started
    And the match target is 4
    And the match has the players "Luca, anna"
    When "@mario" sends "togli luca"
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

  Scenario: scambia finds the players of the teams whatever the case they were stored with
    Given a match was started
    And the match target is 4
    And the match has the players "Anna, bea, Carlo, dino"
    And the match has the black team "Anna, bea" and the white team "Carlo, dino"
    When "@mario" sends "scambia anna con carlo"
    Then the bot should send:
      """
      Perfetto, ho scambiato anna con carlo
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                                |
      | teams | black: bea, Carlo \| white: Anna, dino |

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

  Scenario: aggiungi a,b,c adds every name, and sending the same list again changes nothing
    Given a match was started
    And the match target is 4
    When "@mario" sends "aggiungi a,b,c"
    Then the bot should send:
      """
      Ok, aggiungo a, b e c
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
    And the bot should send nothing else
    When "@mario" sends "aggiungi a,b,c"
    Then the bot should send:
      """
      a, b e c sono già nella lista
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value   |
      | players | a, b, c |

  Scenario: aggiungi trims the names and skips the empty ones
    Given a match was started
    And the match target is 4
    When "@mario" sends "Aggiungi  Anna , bea,, ,Carlo ,"
    Then the bot should send:
      """
      Ok, aggiungo anna, bea e carlo
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. bea ✅
      3. carlo ✅
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value           |
      | players | anna, bea, carlo |

  Scenario: aggiungi a list applies to each name the rule of a single name
    Given a match was started
    And the match target is 4
    And the match has the players "anna, bea (maybe)"
    When "@mario" sends "aggiungi anna,bea,carlo,anna"
    Then the bot should send:
      """
      Ok, aggiungo carlo. Ok, bea, ti confermo. anna è già nella lista
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. bea ✅
      3. carlo ✅
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value            |
      | players | anna, bea, carlo |

  Scenario: aggiungi a list stops adding when the list is full and kicks off the match
    Given a match was started
    And the match target is 2
    And the match has the players "anna"
    When "@mario" sends "aggiungi bea,carlo,dino"
    Then the bot should send:
      """
      Ok, aggiungo bea. Ma aspetta! Non posso aggiungere carlo e dino perché siete già in 2
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. bea ✅

      {footer}
      """
    And the bot should pin the last message
    And the bot should send the text "kickoff"
    And the bot should send nothing else
    And the match should have:
      | field   | value     |
      | players | anna, bea |

  Scenario: aggiungi a list tells apart the names added and the ones already in the list
    Given a match was started
    And the match target is 4
    And the match has the players "a, b"
    When "@mario" sends "aggiungi a,b,c"
    Then the bot should send:
      """
      Ok, aggiungo c. a e b sono già nella lista
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
    And the bot should send nothing else

  Scenario: aggiungi a list confirms together two names that were maybe present
    Given a match was started
    And the match target is 4
    And the match has the players "a (maybe), b (maybe)"
    When "@mario" sends "aggiungi a,b"
    Then the bot should send:
      """
      Ok, a e b, vi confermo
      """
    And the bot should send:
      """
      {header}

      1. a ✅
      2. b ✅
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value |
      | players | a, b  |

  Scenario: aggiungi a list that fills up mid-message refuses the one name left out
    Given a match was started
    And the match target is 2
    When "@mario" sends "aggiungi a,b,c"
    Then the bot should send:
      """
      Ok, aggiungo a e b. Ma aspetta! Non posso aggiungere c perché siete già in 2
      """
    And the bot should send:
      """
      {header}

      1. a ✅
      2. b ✅

      {footer}
      """
    And the bot should pin the last message
    And the bot should send the text "kickoff"
    And the bot should send nothing else
    And the match should have:
      | field   | value |
      | players | a, b  |

  Scenario: aggiungi a list that fills up mid-message refuses the two names left out
    Given a match was started
    And the match target is 10
    And the match has the players "p1, p2, p3, p4, p5, p6, p7, p8, p9"
    When "@mario" sends "aggiungi a,b,c"
    Then the bot should send:
      """
      Ok, aggiungo a. Ma aspetta! Non posso aggiungere b e c perché siete già in 10
      """
    And the bot should send:
      """
      {header}

      1. p1 ✅
      2. p2 ✅
      3. p3 ✅
      4. p4 ✅
      5. p5 ✅
      6. p6 ✅
      7. p7 ✅
      8. p8 ✅
      9. p9 ✅
      10. a ✅

      {footer}
      """
    And the bot should pin the last message
    And the bot should send the text "kickoff"
    And the bot should send nothing else

  Scenario: aggiungi a list when the list is already full only says so
    Given a match was started
    And the match target is 2
    And the match has the players "anna, bea"
    When "@mario" sends "aggiungi carlo,dino"
    Then the bot should send:
      """
      Siete già in 2
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value     |
      | players | anna, bea |

  Scenario Outline: aggiungi a,b,c groups the names by outcome whatever the initial list (<before>)
    Given a match was started
    And the match target is 10
    And the match has the players "<before>"
    When "@mario" sends "aggiungi a,b,c"
    Then the bot should send:
      """
      <answer>
      """
    And the bot should send:
      """
      {header}

      1. <s1>
      2. <s2>
      3. <s3>
      4. <s4>
      5. ❌
      6. ❌
      7. ❌
      8. ❌
      9. ❌
      10. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value   |
      | players | <after> |

    Examples:
      | before                             | answer                                                  | s1  | s2  | s3  | s4  | after      |
      | z                                  | Ok, aggiungo a, b e c                                   | z ✅ | a ✅ | b ✅ | c ✅ | z, a, b, c |
      | z, a                               | Ok, aggiungo b e c. a è già nella lista                 | z ✅ | a ✅ | b ✅ | c ✅ | z, a, b, c |
      | z, b                               | Ok, aggiungo a e c. b è già nella lista                 | z ✅ | b ✅ | a ✅ | c ✅ | z, b, a, c |
      | z, c                               | Ok, aggiungo a e b. c è già nella lista                 | z ✅ | c ✅ | a ✅ | b ✅ | z, c, a, b |
      | z, a, b                            | Ok, aggiungo c. a e b sono già nella lista              | z ✅ | a ✅ | b ✅ | c ✅ | z, a, b, c |
      | z, b, c                            | Ok, aggiungo a. b e c sono già nella lista              | z ✅ | b ✅ | c ✅ | a ✅ | z, b, c, a |
      | z, a, c                            | Ok, aggiungo b. a e c sono già nella lista              | z ✅ | a ✅ | c ✅ | b ✅ | z, a, c, b |
      | z, a (maybe), b                    | Ok, aggiungo c. Ok, a, ti confermo. b è già nella lista | z ✅ | b ✅ | a ✅ | c ✅ | z, b, a, c |
      | z, a (maybe), b (maybe), c         | Ok, a e b, vi confermo. c è già nella lista             | z ✅ | c ✅ | a ✅ | b ✅ | z, c, a, b |
      | z, a (maybe), b (maybe), c (maybe) | Ok, a, b e c, vi confermo                               | z ✅ | a ✅ | b ✅ | c ✅ | z, a, b, c |

  Scenario: aggiungi a,b,c with all three names already in the list changes nothing
    Given a match was started
    And the match target is 10
    And the match has the players "z, a, b, c"
    When "@mario" sends "aggiungi a,b,c"
    Then the bot should send:
      """
      a, b e c sono già nella lista
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value      |
      | players | z, a, b, c |

  Scenario Outline: aggiungi a,b,c groups the names refused because the list fills up (<before>)
    Given a match was started
    And the match target is 3
    And the match has the players "<before>"
    When "@mario" sends "aggiungi a,b,c"
    Then the bot should send:
      """
      <answer>
      """
    And the bot should send:
      """
      {header}

      1. <s1>
      2. <s2>
      3. <s3>

      {footer}
      """
    And the bot should pin the last message
    And the bot should send the text "kickoff"
    And the bot should send nothing else
    And the match should have:
      | field   | value   |
      | players | <after> |

    Examples:
      | before          | answer                                                                                            | s1  | s2  | s3  | after   |
      | z               | Ok, aggiungo a e b. Ma aspetta! Non posso aggiungere c perché siete già in 3                      | z ✅ | a ✅ | b ✅ | z, a, b |
      | z, a            | Ok, aggiungo b. a è già nella lista. Ma aspetta! Non posso aggiungere c perché siete già in 3 | z ✅ | a ✅ | b ✅ | z, a, b |
      | z, a (maybe), b | Ok, a, ti confermo. b è già nella lista. Ma aspetta! Non posso aggiungere c perché siete già in 3 | z ✅ | b ✅ | a ✅ | z, b, a |

  Scenario Outline: proponi a,b,c groups the names by outcome whatever the initial list (<before>)
    Given a match was started
    And the match target is 10
    And the match has the players "<before>"
    When "@mario" sends "proponi a,b,c"
    Then the bot should send:
      """
      <answer>
      """
    And the bot should send:
      """
      {header}

      1. <s1>
      2. <s2>
      3. <s3>
      4. <s4>
      5. ❌
      6. ❌
      7. ❌
      8. ❌
      9. ❌
      10. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value   |
      | players | <after> |

    Examples:
      | before          | answer                                                         | s1  | s2  | s3  | s4  | after                              |
      | z               | Ok, propongo a, b e c                                          | z ✅ | a ❓ | b ❓ | c ❓ | z, a (maybe), b (maybe), c (maybe) |
      | z, b (maybe)    | Ok, propongo a e c. b è già nella lista                        | z ✅ | b ❓ | a ❓ | c ❓ | z, b (maybe), a (maybe), c (maybe) |
      | z, b, c         | Ok, propongo a. Va bene, metto in forse b e c                  | z ✅ | a ❓ | b ❓ | c ❓ | z, a (maybe), b (maybe), c (maybe) |
      | z, a, b (maybe) | Ok, propongo c. Va bene, metto in forse a. b è già nella lista | z ✅ | b ❓ | a ❓ | c ❓ | z, b (maybe), a (maybe), c (maybe) |

  Scenario: proponi a,b,c with all three names already maybe present changes nothing
    Given a match was started
    And the match target is 10
    And the match has the players "z, a (maybe), b (maybe), c (maybe)"
    When "@mario" sends "proponi a,b,c"
    Then the bot should send:
      """
      a, b e c sono già nella lista
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value                              |
      | players | z, a (maybe), b (maybe), c (maybe) |

  # ---- validation of the names and chatty messages (#61, #93, #94) --------------------------------

  Scenario Outline: A /command among the names is refused as a whole
    Given a match was started
    And the match target is 4
    When "@mario" sends "<message>"
    Then the bot should send:
      """
      Un nome non può iniziare con /
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value  |
      | players | (none) |

    Examples:
      | message             |
      | aggiungi luca,/stop |
      | proponi /stop,luca  |
      | togli /stop         |

  Scenario Outline: <message> without a name asks for one and writes nothing
    Given a match was started
    And the match target is 4
    And the match has the players "anna"
    When "@mario" sends "<message>"
    Then the bot should send:
      """
      <answer>
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value |
      | players | anna  |

    Examples:
      | message      | answer                                        |
      | aggiungi     | Chi dovrei aggiungere? Scrivi: aggiungi <nome> |
      | proponi      | Chi dovrei proporre? Scrivi: proponi <nome>   |
      | togli        | Chi dovrei togliere? Scrivi: togli <nome>     |

  Scenario Outline: <message> with only commas does not write an empty name
    Given a match was started
    And the match target is 4
    When "@mario" sends "<message>"
    Then the bot should send:
      """
      <answer>
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value  |
      | players | (none) |
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

    Examples:
      | message      | answer                                         |
      | aggiungi     | Chi dovrei aggiungere? Scrivi: aggiungi <nome> |
      | aggiungi ,,  | Chi dovrei aggiungere? Scrivi: aggiungi <nome> |
      | proponi ,    | Chi dovrei proporre? Scrivi: proponi <nome>    |

  Scenario Outline: A chatty message starting with a self command is ignored like any other chat
    Given a match was started
    And the match target is 4
    And the match has the players "anna"
    When "@mario" sends "<message>"
    Then the bot should send nothing else
    And the match should have:
      | field   | value |
      | players | anna  |

    Examples:
      | message          |
      | Aggiungimi pure  |
      | toglimi grazie   |
      | proponimi forse  |
      | aggiungimiii     |
      | aggiungiamo luca |
      | togliamo anna    |
      | proponiamo luca  |

  Scenario: A /command written after aggiungi is refused
    Given a match was started
    And the match target is 4
    When "@mario" sends "aggiungi /start"
    Then the bot should send:
      """
      Un nome non può iniziare con /
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value  |
      | players | (none) |

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

  Scenario: proponi a,b,c proposes every name
    Given a match was started
    And the match target is 4
    When "@mario" sends "proponi a,b,c"
    Then the bot should send:
      """
      Ok, propongo a, b e c
      """
    And the bot should send:
      """
      {header}

      1. a ❓
      2. b ❓
      3. c ❓
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value                           |
      | players | a (maybe), b (maybe), c (maybe) |

  Scenario: proponi a list applies to each name the rule of a single name and revokes the teams
    Given a match was started
    And the match target is 4
    And the match has the players "anna, bea (maybe), carlo, dino"
    And the match has the black team "anna, carlo" and the white team "dino"
    When "@mario" sends "proponi anna,bea,anna"
    Then the bot should send:
      """
      Va bene, metto in forse anna. bea è già nella lista
      """
    And the bot should send the text "teams revoked"
    And the bot should send:
      """
      {header}

      1. bea ❓
      2. carlo ✅
      3. dino ✅
      4. anna ❓

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value                                       |
      | players | bea (maybe), carlo, dino, anna (maybe) |
      | teams   | (none)                                      |

  Scenario: proponi a list moves the confirmed names to maybe together
    Given a match was started
    And the match target is 4
    And the match has the players "a, b, c"
    When "@mario" sends "proponi a,b,d"
    Then the bot should send:
      """
      Ok, propongo d. Va bene, metto in forse a e b
      """
    And the bot should send:
      """
      {header}

      1. c ✅
      2. a ❓
      3. b ❓
      4. d ❓

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  Scenario: proponi a list that fills up mid-message refuses the names left out
    Given a match was started
    And the match target is 2
    When "@mario" sends "proponi a,b,c"
    Then the bot should send:
      """
      Ok, propongo a e b. Ma aspetta! Non posso proporre c perché siete già in 2
      """
    And the bot should send:
      """
      {header}

      1. a ❓
      2. b ❓

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  Scenario: proponi a list when the list is already full only says so
    Given a match was started
    And the match target is 2
    And the match has the players "anna, bea"
    When "@mario" sends "proponi carlo,dino"
    Then the bot should send:
      """
      Siete già in 2
      """
    And the bot should send nothing else

  Scenario: proponi a list of names already maybe present does nothing
    Given a match was started
    And the match target is 4
    And the match has the players "a (maybe), b (maybe)"
    When "@mario" sends "proponi a,b"
    Then the bot should send:
      """
      a e b sono già nella lista
      """
    And the bot should send nothing else

  Scenario: A /command written after proponi is refused
    Given a match was started
    And the match target is 4
    When "@mario" sends "proponi /stop"
    Then the bot should send:
      """
      Un nome non può iniziare con /
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value  |
      | players | (none) |

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

  Scenario: A /command written after togli is refused, even if an old entry with that name exists
    Given a match was started
    And the match target is 4
    And the match has the players "/start"
    When "@mario" sends "togli /start"
    Then the bot should send:
      """
      Un nome non può iniziare con /
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value  |
      | players | /start |

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
      | teams | black: bea, carlo \| white: anna, dino |

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
      | teams | black: anna, dino \| white: bea, carlo |

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

  Scenario: scambia with a player who is in the list but not in the teams is refused and drops nobody
    Given a match was started
    And the match target is 6
    And the match has the players "anna, bea, carlo, dino, enzo"
    And the match has the black team "anna, bea" and the white team "carlo, dino"
    When "@mario" sends "scambia anna con enzo"
    Then the bot should send:
      """
      enzo non è in nessuna squadra
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                               |
      | teams | black: anna, bea \| white: carlo, dino |

  Scenario: scambia with a first player who is in the list but not in the teams is refused
    Given a match was started
    And the match target is 6
    And the match has the players "anna, bea, carlo, dino, enzo"
    And the match has the black team "anna, bea" and the white team "carlo, dino"
    When "@mario" sends "scambia enzo con carlo"
    Then the bot should send:
      """
      enzo non è in nessuna squadra
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                               |
      | teams | black: anna, bea \| white: carlo, dino |

  Scenario Outline: scambia with the wrong syntax explains the usage
    Given a match was started
    And the match target is 4
    And the match has the players "anna, bea, carlo, dino"
    And the match has the black team "anna, bea" and the white team "carlo, dino"
    When "@mario" sends "<message>"
    Then the bot should send:
      """
      Per scambiare due giocatori scrivi: scambia <nome 1> con <nome 2>
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                               |
      | teams | black: anna, bea \| white: carlo, dino |

    Examples:
      | message                       |
      | scambia                       |
      | scambia anna                  |
      | scambia anna con              |
      | scambia con anna              |
      | scambia anna con bea con dino |

  Scenario: scambia with the wrong syntax explains the usage even before the teams exist
    Given a match was started
    When "@mario" sends "scambia anna"
    Then the bot should send:
      """
      Per scambiare due giocatori scrivi: scambia <nome 1> con <nome 2>
      """
    And the bot should send nothing else

  Scenario: scambia a player with himself is refused and changes nothing
    Given a match was started
    And the match target is 4
    And the match has the players "anna, bea, carlo, dino"
    And the match has the black team "anna, bea" and the white team "carlo, dino"
    When "@mario" sends "scambia anna con anna"
    Then the bot should send:
      """
      anna e anna sono nella stessa squadra!
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                               |
      | teams | black: anna, bea \| white: carlo, dino |

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

  Scenario: Siete già in N when a maybe present player holds the last place
    Given a match was started
    And the match target is 2
    And the match has the players "anna, bea (maybe)"
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Siete già in 2 (1 in forse)
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value             |
      | players | anna, bea (maybe) |

  Scenario: Siete già in N tells how many players are maybe present
    Given a match was started
    And the match target is 2
    And the match has the players "anna, bea, carlo (maybe), dino (maybe)"
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Siete già in 2 (2 in forse)
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value                                  |
      | players | anna, bea, carlo (maybe), dino (maybe) |

  Scenario: A new player is refused while a maybe present player holds the place
    Given a match was started
    And the match target is 10
    And the match has the players "a, b, c, d, e, f, g, h, i, j (maybe)"
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Siete già in 10 (1 in forse)
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value                                |
      | players | a, b, c, d, e, f, g, h, i, j (maybe) |

  Scenario Outline: <message> while a maybe present player holds the place is refused
    Given a match was started
    And the match target is 3
    And the match has the players "anna, bea, carlo (maybe)"
    When "@mario" sends "<message>"
    Then the bot should send:
      """
      Siete già in 3 (1 in forse)
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value                    |
      | players | anna, bea, carlo (maybe) |

    Examples:
      | message             |
      | aggiungi luca       |
      | aggiungi luca, dino |
      | proponimi           |
      | proponi luca        |
      | proponi luca, dino  |

  Scenario: aggiungi a list says who did not fit without mentioning the maybe present players
    Given a match was started
    And the match target is 3
    And the match has the players "anna, bea (maybe)"
    When "@mario" sends "aggiungi carlo, dino"
    Then the bot should send:
      """
      Ok, aggiungo carlo. Ma aspetta! Non posso aggiungere dino perché siete già in 3
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. bea ❓
      3. carlo ✅

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  Scenario: proponi a list says who did not fit without mentioning the maybe present players
    Given a match was started
    And the match target is 3
    And the match has the players "anna, bea (maybe)"
    When "@mario" sends "proponi carlo, dino"
    Then the bot should send:
      """
      Ok, propongo carlo. Ma aspetta! Non posso proporre dino perché siete già in 3
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. bea ❓
      3. carlo ❓

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  Scenario: A maybe present player who confirms the last place kicks off the match
    Given a match was started
    And the match target is 10
    And the match has the players "a, b, c, d, e, f, g, h, i, @mario (maybe)"
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Ok, @mario, ti confermo
      """
    And the bot should send:
      """
      {header}

      1. a ✅
      2. b ✅
      3. c ✅
      4. d ✅
      5. e ✅
      6. f ✅
      7. g ✅
      8. h ✅
      9. i ✅
      10. @mario ✅

      {footer}
      """
    And the bot should pin the summary
    And the bot should send the text "kickoff"
    And the bot should send nothing else

  Scenario: A full list with a maybe present player does not kick off with aggiungimi
    Given a match was started
    And the match target is 3
    And the match has the players "anna, bea (maybe)"
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Ok, @mario, ti aggiungo
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. bea ❓
      3. @mario ✅

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  Scenario: A full list with a maybe present player does not kick off with aggiungi
    Given a match was started
    And the match target is 3
    And the match has the players "anna, bea (maybe)"
    When "@mario" sends "aggiungi carlo"
    Then the bot should send:
      """
      Ok, aggiungo carlo
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. bea ❓
      3. carlo ✅

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

  # ---- order of the list and names differing only in case ----------------------------------------

  Scenario: aggiungimi moves a maybe present sender after the players who follow him
    Given a match was started
    And the match target is 6
    And the match has the players "anna, @mario (maybe), luca, sara"
    When "@mario" sends "aggiungimi"
    Then the bot should send:
      """
      Ok, @mario, ti confermo
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. luca ✅
      3. sara ✅
      4. @mario ✅
      5. ❌
      6. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value                    |
      | players | anna, luca, sara, @mario |

  Scenario: aggiungi <nome> moves a maybe present name after the players who follow it
    Given a match was started
    And the match target is 6
    And the match has the players "anna, luca (maybe), sara (maybe), bea"
    When "@mario" sends "aggiungi luca"
    Then the bot should send:
      """
      Ok, luca, ti confermo
      """
    And the bot should send:
      """
      {header}

      1. anna ✅
      2. sara ❓
      3. bea ✅
      4. luca ✅
      5. ❌
      6. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value                         |
      | players | anna, sara (maybe), bea, luca |

  Scenario: A name added after a player in the middle was removed goes last
    Given a match was started
    And the match target is 6
    And the match has the players "anna, bea, carlo"
    And "@mario" had sent "/participants"
    When "@mario" sends "togli bea"
    Then the bot should send:
      """
      Che vergogna, bea
      """
    And the bot should edit the summary to:
      """
      {header}

      1. anna ✅
      2. carlo ✅
      3. ❌
      4. ❌
      5. ❌
      6. ❌

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    When "@mario" sends "aggiungi dino"
    Then the bot should send:
      """
      Ok, aggiungo dino
      """
    And the bot should edit the summary to:
      """
      {header}

      1. anna ✅
      2. carlo ✅
      3. dino ✅
      4. ❌
      5. ❌
      6. ❌

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match should have:
      | field   | value             |
      | players | anna, carlo, dino |

  Scenario: A removed name that is added again goes last
    Given a match was started
    And the match target is 6
    And the match has the players "anna, bea, carlo"
    And "@mario" had sent "/participants"
    When "@mario" sends "togli anna"
    Then the bot should send:
      """
      Che vergogna, anna
      """
    And the bot should edit the summary to:
      """
      {header}

      1. bea ✅
      2. carlo ✅
      3. ❌
      4. ❌
      5. ❌
      6. ❌

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    When "@mario" sends "aggiungi anna"
    Then the bot should send:
      """
      Ok, aggiungo anna
      """
    And the bot should edit the summary to:
      """
      {header}

      1. bea ✅
      2. carlo ✅
      3. anna ✅
      4. ❌
      5. ❌
      6. ❌

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match should have:
      | field   | value            |
      | players | bea, carlo, anna |

  Scenario: A sender who removed himself and comes back goes last, as maybe present too
    Given a match was started
    And the match target is 6
    And the match has the players "anna, @mario, carlo"
    And "@mario" had sent "/participants"
    When "@mario" sends "toglimi"
    Then the bot should send:
      """
      Mamma mia... che paccaro
      """
    And the bot should edit the summary to:
      """
      {header}

      1. anna ✅
      2. carlo ✅
      3. ❌
      4. ❌
      5. ❌
      6. ❌

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    When "@mario" sends "proponimi"
    Then the bot should send:
      """
      Ok, @mario, ti propongo
      """
    And the bot should edit the summary to:
      """
      {header}

      1. anna ✅
      2. carlo ✅
      3. @mario ❓
      4. ❌
      5. ❌
      6. ❌

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match should have:
      | field   | value                       |
      | players | anna, carlo, @mario (maybe) |

  Scenario: proponi puts in forse the player who was added with another case, without a second person
    Given a match was started
    And the match target is 4
    And the match has the players "Luca"
    When "@mario" sends "proponi luca"
    Then the bot should send:
      """
      Va bene, metto in forse luca
      """
    And the bot should send:
      """
      {header}

      1. Luca ❓
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value   |
      | players | Luca (maybe) |

  Scenario: proponi on a maybe present player added with another case says he is already maybe present
    Given a match was started
    And the match target is 4
    And the match has the players "Luca (maybe)"
    When "@mario" sends "proponi luca"
    Then the bot should send:
      """
      luca è già nella lista
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value   |
      | players | Luca (maybe) |

  Scenario: aggiungi confirms the maybe present player who was added with another case
    Given a match was started
    And the match target is 4
    And the match has the players "Luca (maybe)"
    When "@mario" sends "aggiungi luca"
    Then the bot should send:
      """
      Ok, luca, ti confermo
      """
    And the bot should send:
      """
      {header}

      1. Luca ✅
      2. ❌
      3. ❌
      4. ❌

      {footer}
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field   | value   |
      | players | Luca |

  Scenario: aggiungimi sees a sender without username as already in the list next to an entry with another case
    Given a match was started
    And the match target is 4
    And a user named "Luca" without username
    And the match has the players "luca"
    When "Luca" sends "aggiungimi"
    Then the bot should send:
      """
      Ma Luca, sei già nella lista
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value   |
      | players | luca |

  Scenario: proponimi puts in forse a sender without username who was added with another case
    Given a match was started
    And the match target is 4
    And a user named "Luca" without username
    And the match has the players "luca"
    When "Luca" sends "proponimi"
    Then the bot should send:
      """
      Ok, Luca, ti metto in forse
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
      | field   | value   |
      | players | luca (maybe) |

  Scenario: proponimi on a sender without username maybe present with another case says he is already maybe present
    Given a match was started
    And the match target is 4
    And a user named "Luca" without username
    And the match has the players "luca (maybe)"
    When "Luca" sends "proponimi"
    Then the bot should send:
      """
      Ma Luca, sei già in forse
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value   |
      | players | luca (maybe) |

  Scenario: toglimi removes a sender without username who is stored with another case
    Given a match was started
    And the match target is 4
    And a user named "Luca" without username
    And the match has the players "luca (maybe), anna"
    When "Luca" sends "toglimi"
    Then the bot should send:
      """
      Peccato, un po' ci avevo sperato
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
      | field   | value   |
      | players | anna |

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
