Feature: Teams
  /teams draws two teams (black and white) once the list is complete and the target is even.
  The teams are kept until the list or the target changes, and can be adjusted with "scambia".

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
    And the text "footer" is:
      """
      {default description}

      *CAMPO*: 
      Usa il comando /setpitch <campo> per inserire la struttura sportiva dove giocherete.
      """
    And the text "full list of 4" is:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. ale ✅
      2. bea ✅
      3. carlo ✅
      4. dino ✅

      {footer}
      """
    And the text "teams ale and dino against bea and carlo" is:
      """
      *SQUADRA NERA* 
       - ale
       - dino

      *SQUADRA BIANCA* 
       - bea
       - carlo

      """
    And the text "no match" is:
      """
      Prima di iniziare con le danze, avvia una partita, per farlo usa /start
      """
    And the text "teams cancelled" is:
      """
      *SQUADRE ANNULLATE*
      """

  Scenario: /teams before /start is refused and does not create a match
    When "@mario" sends "/teams"
    Then the bot should send the text "no match"
    And the bot should send nothing else
    And there should be no match for this chat

  Scenario: /teams with an empty list asks to reach the target
    Given a match was started
    And the match target is 4
    When "@mario" sends "/teams"
    Then the bot should send:
      """
      Prima di poter fare le squadre, devi raggiungere 4 partecipanti
      """
    And the bot should send nothing else
    And the match should have:
      | field | value  |
      | teams | (none) |

  Scenario: /teams with an incomplete list asks to reach the target
    Given a match was started
    And the match has the players "ale, bea, carlo"
    When "@mario" sends "/teams"
    Then the bot should send:
      """
      Prima di poter fare le squadre, devi raggiungere 10 partecipanti
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value          |
      | players | ale, bea, carlo |
      | teams   | (none)         |

  Scenario: /teams does not count the maybe-present people as participants
    Given a match was started
    And the match target is 4
    And the match has the players "ale, bea, carlo"
    And "@mario" had sent "proponi dino"
    When "@mario" sends "/teams"
    Then the bot should send:
      """
      Prima di poter fare le squadre, devi raggiungere 4 partecipanti
      """
    And the bot should send nothing else
    And the match should have:
      | field | value  |
      | teams | (none) |

  Scenario: /teams with an odd target refuses, even with a complete list
    Given a match was started
    And the match has the players "ale, bea, carlo"
    And the match target is 3
    When "@mario" sends "/teams"
    Then the bot should send:
      """
      Per usare questa funzionalità dovete essere in un numero pari di partecipanti
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value           |
      | players | ale, bea, carlo |
      | target  | 3               |
      | teams   | (none)          |

  Scenario: /teams with an odd target and an incomplete list refuses for the odd target first
    Given a match was started
    And the match target is 5
    When "@mario" sends "/teams"
    Then the bot should send:
      """
      Per usare questa funzionalità dovete essere in un numero pari di partecipanti
      """
    And the bot should send nothing else
    And the match should have:
      | field | value  |
      | teams | (none) |

  Scenario: /teams with a complete even list draws and saves the two teams
    Given the team draw is seeded with 42
    And a match was started
    And the match has the players "ale, bea, carlo, dino"
    And the match target is 4
    When "@mario" sends "/teams"
    Then the bot should send the text "teams ale and dino against bea and carlo"
    And the bot should send nothing else
    And the match should have:
      | field   | value                                  |
      | players | ale, bea, carlo, dino                  |
      | teams   | black: ale, dino \| white: bea, carlo |

  Scenario: /teams again shows the same teams instead of drawing new ones
    Given the team draw is seeded with 42
    And a match was started
    And the match has the players "ale, bea, carlo, dino"
    And the match target is 4
    And "@mario" had sent "/teams"
    And the team draw is seeded with 7
    When "@mario" sends "/teams"
    Then the bot should send the text "teams ale and dino against bea and carlo"
    And the bot should send nothing else
    And the match should have:
      | field | value                                  |
      | teams | black: ale, dino \| white: bea, carlo |

  Scenario: Removing a player from the list cancels the teams
    Given the team draw is seeded with 42
    And a match was started
    And the match has the players "ale, bea, carlo, dino"
    And the match target is 4
    And "@mario" had sent "/participants"
    And "@mario" had sent "/teams"
    When "@mario" sends "togli ale"
    Then the bot should send:
      """
      Che vergogna, ale
      """
    And the bot should send the text "teams cancelled"
    And the bot should edit the summary to:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. bea ✅
      2. carlo ✅
      3. dino ✅
      4. ❌

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match should have:
      | field | value  |
      | teams | (none) |
    When "@mario" sends "/teams"
    Then the bot should send:
      """
      Prima di poter fare le squadre, devi raggiungere 4 partecipanti
      """
    And the bot should send nothing else

  Scenario: Putting a player in maybe cancels the teams
    Given the team draw is seeded with 42
    And a match was started
    And the match has the players "ale, bea, carlo, dino"
    And the match target is 4
    And "@mario" had sent "/participants"
    And "@mario" had sent "/teams"
    When "@mario" sends "proponi dino"
    Then the bot should send:
      """
      Va bene, metto in forse dino
      """
    And the bot should send the text "teams cancelled"
    And the bot should edit the summary to:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. ale ✅
      2. bea ✅
      3. carlo ✅
      4. dino ❓

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match should have:
      | field   | value                         |
      | players | ale, bea, carlo, dino (maybe) |
      | teams   | (none)                        |

  Scenario: A full list does not accept more players and keeps the teams
    Given the team draw is seeded with 42
    And a match was started
    And the match has the players "ale, bea, carlo, dino"
    And the match target is 4
    And "@mario" had sent "/teams"
    When "@mario" sends "aggiungi eva"
    Then the bot should send:
      """
      Siete già in 4
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                                  |
      | teams | black: ale, dino \| white: bea, carlo |

  Scenario: Changing the target cancels the teams
    Given the team draw is seeded with 42
    And a match was started
    And the match has the players "ale, bea, carlo, dino"
    And the match target is 4
    And "@mario" had sent "/participants"
    And "@mario" had sent "/teams"
    When "@mario" sends "/setnumber 6"
    Then the bot should send the text "teams cancelled"
    And the bot should edit the summary to:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. ale ✅
      2. bea ✅
      3. carlo ✅
      4. dino ✅
      5. ❌
      6. ❌

      {footer}
      """
    And the bot should pin the summary
    And the bot should send:
      """
      Ok, @mario! Ho impostato il numero di partecipanti a 6
      """
    And the bot should send nothing else
    And the match should have:
      | field  | value  |
      | target | 6      |
      | teams  | (none) |
    When "@mario" sends "/teams"
    Then the bot should send:
      """
      Prima di poter fare le squadre, devi raggiungere 6 partecipanti
      """
    And the bot should send nothing else

  Scenario: Setting the same target again cancels the teams and invites to draw them again
    Given the team draw is seeded with 42
    And a match was started
    And the match has the players "ale, bea, carlo, dino"
    And the match target is 4
    And "@mario" had sent "/participants"
    And "@mario" had sent "/teams"
    When "@mario" sends "/setnumber 4"
    Then the bot should send the text "teams cancelled"
    And the bot should edit the summary to:
      """
      {full list of 4}
      """
    And the bot should pin the summary
    And the bot should send:
      """
      🚀 *SI GIOCA* 🚀 facciamo le squadre? /teams 😎
      """
    And the bot should send:
      """
      Ok, @mario! Ho impostato il numero di partecipanti a 4
      """
    And the bot should send nothing else
    And the match should have:
      | field | value  |
      | teams | (none) |

  Scenario: After the teams are cancelled a new draw is possible once the list is complete again
    Given the team draw is seeded with 42
    And a match was started
    And the match has the players "ale, bea, carlo, dino"
    And the match target is 4
    And "@mario" had sent "/teams"
    And "@mario" had sent "togli ale"
    And "@mario" had sent "aggiungi ale"
    And the team draw is seeded with 7
    When "@mario" sends "/teams"
    Then the bot should send:
      """
      *SQUADRA NERA* 
       - dino
       - bea

      *SQUADRA BIANCA* 
       - carlo
       - ale

      """
    And the bot should send nothing else
    And the match should have:
      | field   | value                                  |
      | players | bea, carlo, dino, ale                  |
      | teams   | black: bea, dino \| white: carlo, ale |

  Scenario: scambia moves two players of different teams to each other's team
    Given the team draw is seeded with 42
    And a match was started
    And the match has the players "ale, bea, carlo, dino"
    And the match target is 4
    And "@mario" had sent "/teams"
    When "@mario" sends "scambia ale con bea"
    Then the bot should send:
      """
      Perfetto, ho scambiato ale con bea
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                                  |
      | teams | black: bea, dino \| white: ale, carlo |
    When "@mario" sends "/teams"
    Then the bot should send:
      """
      *SQUADRA NERA* 
       - bea
       - dino

      *SQUADRA BIANCA* 
       - ale
       - carlo

      """
    And the bot should send nothing else

  Scenario: scambia works in both directions (white player first)
    Given the team draw is seeded with 42
    And a match was started
    And the match has the players "ale, bea, carlo, dino"
    And the match target is 4
    And "@mario" had sent "/teams"
    When "@mario" sends "scambia carlo con bea"
    Then the bot should send:
      """
      carlo e bea sono nella stessa squadra!
      """
    And the bot should send nothing else
    When "@mario" sends "scambia carlo con ale"
    Then the bot should send:
      """
      Perfetto, ho scambiato carlo con ale
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                                  |
      | teams | black: carlo, dino \| white: ale, bea |

  Scenario: scambia between two players of the same team is refused and changes nothing
    Given the team draw is seeded with 42
    And a match was started
    And the match has the players "ale, bea, carlo, dino"
    And the match target is 4
    And "@mario" had sent "/teams"
    When "@mario" sends "scambia ale con dino"
    Then the bot should send:
      """
      ale e dino sono nella stessa squadra!
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                                  |
      | teams | black: ale, dino \| white: bea, carlo |

  Scenario Outline: scambia with a name that is not in the list is refused
    Given the team draw is seeded with 42
    And a match was started
    And the match has the players "ale, bea, carlo, dino"
    And the match target is 4
    And "@mario" had sent "/teams"
    When "@mario" sends "<message>"
    Then the bot should send:
      """
      <answer>
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                                  |
      | teams | black: ale, dino \| white: bea, carlo |

    Examples:
      | message              | answer       |
      | scambia ale con zeno | zeno non c'è |
      | scambia zeno con ale | zeno non c'è |

  Scenario Outline: A chatty message starting with scambia is ignored like any other chat
    Given the team draw is seeded with 42
    And a match was started
    And the match has the players "ale, bea, carlo, dino"
    And the match target is 4
    And "@mario" had sent "/teams"
    When "@mario" sends "<message>"
    Then the bot should send nothing else
    And the match should have:
      | field | value                                  |
      | teams | black: ale, dino \| white: bea, carlo |

    Examples:
      | message                |
      | scambiamo anna con bea |
      | scambiare le maglie    |
      | Scambiamo?             |

  Scenario: scambia before the teams exist explains that the teams are needed
    Given a match was started
    And the match has the players "ale, bea, carlo, dino"
    And the match target is 4
    When "@mario" sends "scambia ale con bea"
    Then the bot should send:
      """
      Per usare questa funzionalità devi prima formare delle squadre con /teams
      """
    And the bot should send nothing else
    And the match should have:
      | field | value  |
      | teams | (none) |

  Scenario: scambia before /start is refused
    When "@mario" sends "scambia ale con bea"
    Then the bot should send the text "no match"
    And the bot should send nothing else
    And there should be no match for this chat

  Scenario: /teams draws only the confirmed players when the target was lowered
    # The maybe-present people (carlo, dino) are left out of the draw.
    Given the team draw is seeded with 42
    And a match was started
    And the match target is 4
    And the match has the players "ale, bea"
    And "@mario" had sent "proponi carlo"
    And "@mario" had sent "proponi dino"
    And the match target is 2
    When "@mario" sends "/teams"
    Then the bot should send:
      """
      *SQUADRA NERA* 
       - ale

      *SQUADRA BIANCA* 
       - bea

      """
    And the bot should send nothing else
    And the match should have:
      | field   | value                                 |
      | players | ale, bea, carlo (maybe), dino (maybe) |
      | teams   | black: ale \| white: bea              |

  Scenario: Removing a maybe present player who is not in the teams cancels the teams too
    Given the team draw is seeded with 42
    And a match was started
    And the match target is 4
    And the match has the players "ale, bea"
    And "@mario" had sent "proponi carlo"
    And "@mario" had sent "proponi dino"
    And the match target is 2
    And "@mario" had sent "/participants"
    And "@mario" had sent "/teams"
    When "@mario" sends "togli carlo"
    Then the bot should send:
      """
      Davvero? Ma carlo, ne sei proprio sicuro?
      """
    And the bot should send the text "teams cancelled"
    And the bot should edit the summary to:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. ale ✅
      2. bea ✅

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match should have:
      | field   | value                    |
      | players | ale, bea, dino (maybe)   |
      | teams   | (none)                   |

  # Covers a state created before #128 (a target below the people in the list) that /setnumber now refuses: legacy data may still hold it.
  @known-bug @issue-128
  Scenario: Confirming a maybe present player keeps the teams, even beyond the target, and the summary hides him
    Given the team draw is seeded with 42
    And a match was started
    And the match target is 4
    And the match has the players "ale, bea"
    And "@mario" had sent "proponi carlo"
    And "@mario" had sent "proponi dino"
    And the match target is 2
    And "@mario" had sent "/participants"
    And "@mario" had sent "/teams"
    When "@mario" sends "aggiungi carlo"
    Then the bot should send:
      """
      Ok, carlo, ti confermo
      """
    And the bot should edit the summary to:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. ale ✅
      2. bea ✅

      {footer}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match should have:
      | field   | value                                  |
      | players | ale, bea, dino (maybe), carlo          |
      | teams   | black: ale \| white: bea               |
    When "@mario" sends "/teams"
    Then the bot should send:
      """
      *SQUADRA NERA* 
       - ale

      *SQUADRA BIANCA* 
       - bea

      """
    And the bot should send nothing else
