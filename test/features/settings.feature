Feature: Match settings
  /setnumber, /setday, /settime, /setpitch and /setdescription change the match and then show the
  updated summary: the first time it is sent (and pinned), afterwards the same message is edited.
  Without a match every one of them refuses to work.

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
    And the text "pitch hint" is:
      """
      Usa il comando /setpitch <campo> per inserire la struttura sportiva dove giocherete.
      """
    And the text "default tail" is:
      """
      {default description}

      *CAMPO*: 
      {pitch hint}
      """
    And the text "ten empty slots" is:
      """
      1. ❌
      2. ❌
      3. ❌
      4. ❌
      5. ❌
      6. ❌
      7. ❌
      8. ❌
      9. ❌
      10. ❌
      """
    And the text "welcome" is:
      """
      Ciao bestie 😎, chi c'è per il prossimo calcetto? 

      - se sei in forse scrivi _proponimi_, 
      - se vuoi proporre qualcuno scrivi _proponi <nome>_, 
      - per essere aggiunto o confermato rispondi _aggiungimi_,
      - per aggiungere o confermare qualcuno usa _aggiungi <nome>_,
      - per essere rimosso _toglimi_, 
      - per rimuovere qualcuno _togli <nome>_, 
      - per modificare le squadre scrivi _scambia <nome 1> con <nome 2>_. 

      Posso anche pinnare i messaggi se vuoi ma per farlo ricordati di aggiungermi come amministratore.
      """
    And the text "no match" is:
      """
      Prima di iniziare con le danze, avvia una partita, per farlo usa /start
      """
    And the text "payment reminder" is:
      """
      Ciao bestie 😎, com'è andata la partita? C'è qualcuno che non ha ancora pagato la sua quota?
      """
    And the text "si gioca" is:
      """
      🚀 *SI GIOCA* 🚀 facciamo le squadre? /teams 😎
      """

  # ---- guard: no match yet ---------------------------------------------------------------------

  Scenario Outline: <command> before /start is refused and does not create a match
    When "@mario" sends "<command>"
    Then the bot should send the text "no match"
    And the bot should send nothing else
    And there should be no match for this chat

    Examples:
      | command                 |
      | /setnumber 12           |
      | /setnumber              |
      | /setday 25/10/2026      |
      | /setday                 |
      | /settime 21:30          |
      | /settime                |
      | /setpitch Crespi        |
      | /setpitch               |
      | /setdescription Ciao    |
      | /setdescription         |

  # ---- /setnumber ------------------------------------------------------------------------------

  Scenario: /setnumber changes the target, sends and pins the summary, then confirms
    Given a match was started
    When "@mario" sends "/setnumber 4"
    Then the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. ❌
      2. ❌
      3. ❌
      4. ❌

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send:
      """
      Ok, @mario! Ho impostato il numero di partecipanti a 4
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value |
      | target  | 4     |
      | players | (none) |

  Scenario: The summary is sent only once, then every change edits that same message
    Given a match was started
    When "@mario" sends "/setnumber 4"
    Then the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. ❌
      2. ❌
      3. ❌
      4. ❌

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send:
      """
      Ok, @mario! Ho impostato il numero di partecipanti a 4
      """
    When "@mario" sends "/setnumber 3"
    Then the bot should edit the summary to:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. ❌
      2. ❌
      3. ❌

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send:
      """
      Ok, @mario! Ho impostato il numero di partecipanti a 3
      """
    And the bot should send nothing else
    And the match should have:
      | field  | value |
      | target | 3     |

  Scenario: /setnumber 2 is the lower limit
    Given a match was started
    When "@mario" sends "/setnumber 2"
    Then the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. ❌
      2. ❌

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send:
      """
      Ok, @mario! Ho impostato il numero di partecipanti a 2
      """
    And the bot should send nothing else
    And the match should have:
      | field  | value |
      | target | 2     |

  Scenario: /setnumber 40 is the upper limit
    Given a match was started
    When "@mario" sends "/setnumber 40"
    Then the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. ❌
      2. ❌
      3. ❌
      4. ❌
      5. ❌
      6. ❌
      7. ❌
      8. ❌
      9. ❌
      10. ❌
      11. ❌
      12. ❌
      13. ❌
      14. ❌
      15. ❌
      16. ❌
      17. ❌
      18. ❌
      19. ❌
      20. ❌
      21. ❌
      22. ❌
      23. ❌
      24. ❌
      25. ❌
      26. ❌
      27. ❌
      28. ❌
      29. ❌
      30. ❌
      31. ❌
      32. ❌
      33. ❌
      34. ❌
      35. ❌
      36. ❌
      37. ❌
      38. ❌
      39. ❌
      40. ❌

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send:
      """
      Ok, @mario! Ho impostato il numero di partecipanti a 40
      """
    And the bot should send nothing else
    And the match should have:
      | field  | value |
      | target | 40    |

  Scenario Outline: /setnumber <number> is out of range and changes nothing
    Given a match was started
    When "@mario" sends "/setnumber <number>"
    Then the bot should send:
      """
      <answer>
      """
    And the bot should send nothing else
    And the match should have:
      | field           | value  |
      | target          | 10     |
      | summary message | (none) |

    Examples:
      | number | answer                                    |
      | 0      | Non è un numero valido di partecipanti 🌚 |
      | 41     | Non è un numero valido di partecipanti 🌚 |
      | 1000   | Non è un numero valido di partecipanti 🌚 |
      | 1      | Il numero che hai inserito non va bene 👎 |

  Scenario Outline: /setnumber <text> is not a number
    Given a match was started
    When "@mario" sends "/setnumber <text>"
    Then the bot should send:
      """
      @mario, quello ti sembra un numero? 😂
      """
    And the bot should send nothing else
    And the match should have:
      | field  | value |
      | target | 10    |

    Examples:
      | text |
      | abc  |
      | -3   |
      | 3.5  |
      | 1e1  |

  Scenario: /setnumber without argument explains the usage
    Given a match was started
    When "@mario" sends "/setnumber"
    Then the bot should send:
      """
      Non hai inserito il numero: scrivi /setnumber <numero>
      """
    And the bot should send nothing else
    And the match should have:
      | field  | value |
      | target | 10    |

  Scenario: /setnumber with more than one argument suggests the first one
    Given a match was started
    When "@mario" sends "/setnumber 5 6"
    Then the bot should send:
      """
      Hai messo più di un numero, probabilmente intendevi /setnumber 5
      """
    And the bot should send nothing else
    And the match should have:
      | field  | value |
      | target | 10    |

  Scenario: /setnumber below the number of confirmed players is refused
    Given a match was started
    And "@mario" had sent "aggiungi anna"
    And "@mario" had sent "aggiungi bea"
    And "@mario" had sent "aggiungi carla"
    When "@mario" sends "/setnumber 2"
    Then the bot should send:
      """
      Hai ridotto i partecipanti ma c'è ancora gente nella lista. Io non saprei chi togliere, puoi farlo tu? 🙏
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value             |
      | target  | 10                |
      | players | anna, bea, carla  |

  Scenario: Players who are only maybe-present do not count when lowering the target
    Given a match was started
    And "@mario" had sent "aggiungi anna"
    And "@mario" had sent "aggiungi bea"
    And "@mario" had sent "proponi carla"
    When "@mario" sends "/setnumber 2"
    Then the bot should edit the summary to:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. anna ✅
      2. bea ✅

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send the text "si gioca"
    And the bot should send:
      """
      Ok, @mario! Ho impostato il numero di partecipanti a 2
      """
    And the bot should send nothing else
    And the match should have:
      | field   | value                |
      | target  | 2                    |
      | players | anna, bea, carla (maybe) |

  Scenario: Reaching the target announces that the match is on
    Given a match was started
    And "@mario" had sent "aggiungi anna"
    And "@mario" had sent "aggiungi bea"
    When "@mario" sends "/setnumber 2"
    Then the bot should edit the summary to:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. anna ✅
      2. bea ✅

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send the text "si gioca"
    And the bot should send:
      """
      Ok, @mario! Ho impostato il numero di partecipanti a 2
      """
    And the bot should send nothing else

  Scenario: Setting a number above the players does not announce the match
    Given a match was started
    And "@mario" had sent "aggiungi anna"
    And "@mario" had sent "aggiungi bea"
    When "@mario" sends "/setnumber 3"
    Then the bot should edit the summary to:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. anna ✅
      2. bea ✅
      3. ❌

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send:
      """
      Ok, @mario! Ho impostato il numero di partecipanti a 3
      """
    And the bot should send nothing else

  @known-bug @issue-89
  Scenario: Reaching the target after /setday schedules a second payment reminder, so it is sent twice
    Given a match was started
    And "@mario" had sent "/setday 25/10/2026"
    And "@mario" had sent "aggiungi anna"
    And "@mario" had sent "aggiungi bea"
    When "@mario" sends "/setnumber 2"
    Then the bot should edit the summary to:
      """
      *GIORNO*: 25/10/2026 | 20:00

      1. anna ✅
      2. bea ✅

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send the text "si gioca"
    And the bot should send:
      """
      Ok, @mario! Ho impostato il numero di partecipanti a 2
      """
    When the scheduled jobs run
    Then the bot should send plain text:
      """
      {payment reminder}
      """
    And the bot should pin the last message
    And the bot should send plain text:
      """
      {payment reminder}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  @known-bug @issue-8
  Scenario: Reaching the target with the default day never schedules the payment reminder
    Given a match was started
    And "@mario" had sent "aggiungi anna"
    And "@mario" had sent "aggiungi bea"
    When "@mario" sends "/setnumber 2"
    Then the bot should edit the summary to:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. anna ✅
      2. bea ✅

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send the text "si gioca"
    And the bot should send:
      """
      Ok, @mario! Ho impostato il numero di partecipanti a 2
      """
    When the scheduled jobs run
    Then the bot should send nothing else

  Scenario: Changing the target cancels the teams and the payment reminder
    Given a match was started
    And "@mario" had sent "/setday 25/10/2026"
    And "@mario" had sent "/setnumber 2"
    And "@mario" had sent "aggiungi anna"
    And "@mario" had sent "aggiungi bea"
    And "@mario" had sent "/teams"
    When "@mario" sends "/setnumber 4"
    Then the bot should send:
      """
      *SQUADRE ANNULLATE*
      """
    And the bot should edit the summary to:
      """
      *GIORNO*: 25/10/2026 | 20:00

      1. anna ✅
      2. bea ✅
      3. ❌
      4. ❌

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send:
      """
      Ok, @mario! Ho impostato il numero di partecipanti a 4
      """
    And the bot should send nothing else
    And the match should have:
      | field  | value |
      | target | 4     |
      | teams  | (none) |
    When the scheduled jobs run
    Then the bot should send nothing else

  Scenario: Changing the target to the number of players cancels the teams and announces the match again
    Given a match was started
    And "@mario" had sent "/setnumber 2"
    And "@mario" had sent "aggiungi anna"
    And "@mario" had sent "aggiungi bea"
    And "@mario" had sent "/teams"
    When "@mario" sends "/setnumber 2"
    Then the bot should send:
      """
      *SQUADRE ANNULLATE*
      """
    And the bot should edit the summary to:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      1. anna ✅
      2. bea ✅

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send the text "si gioca"
    And the bot should send:
      """
      Ok, @mario! Ho impostato il numero di partecipanti a 2
      """
    And the bot should send nothing else
    And the match should have:
      | field  | value  |
      | teams  | (none) |

  # ---- /setday ---------------------------------------------------------------------------------

  Scenario: /setday with a date sets it, confirms, then sends and pins the summary
    Given a match was started
    When "@mario" sends "/setday 25/10/2026"
    Then the bot should send:
      """
      Ok, @mario! Ho impostato il giorno della partita il 25/10/2026
      """
    And the bot should send:
      """
      *GIORNO*: 25/10/2026 | 20:00

      {ten empty slots}

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match should have:
      | field | value      |
      | day   | 25/10/2026 |
      | time  | 20:00      |

  Scenario: /setday accepts free text, joins the words and schedules no reminder
    Given a match was started
    When "@mario" sends "/setday sabato   prossimo   sera"
    Then the bot should send:
      """
      Ok, @mario! Ho impostato il giorno della partita il sabato prossimo sera
      """
    And the bot should send:
      """
      *GIORNO*: sabato prossimo sera | 20:00

      {ten empty slots}

      {default tail}
      """
    And the bot should pin the summary
    And the match should have:
      | field | value                |
      | day   | sabato prossimo sera |
    When the scheduled jobs run
    Then the bot should send nothing else

  Scenario: /setday escapes Markdown characters in the confirmation and in the summary
    Given a match was started
    When "@mario" sends "/setday sabato_sera"
    Then the bot should send:
      """
      Ok, @mario! Ho impostato il giorno della partita il sabato\_sera
      """
    And the bot should send:
      """
      *GIORNO*: sabato\_sera | 20:00

      {ten empty slots}

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match should have:
      | field | value       |
      | day   | sabato_sera |

  Scenario: /setday after the summary exists edits it
    Given a match was started
    And "@mario" had sent "/setpitch Crespi"
    When "@mario" sends "/setday 25/10/2026"
    Then the bot should send:
      """
      Ok, @mario! Ho impostato il giorno della partita il 25/10/2026
      """
    And the bot should edit the summary to:
      """
      *GIORNO*: 25/10/2026 | 20:00

      {ten empty slots}

      {default description}

      *CAMPO*: 
      Crespi
      """
    And the bot should pin the summary
    And the bot should send nothing else

  Scenario: /setday without argument explains the usage
    Given a match was started
    When "@mario" sends "/setday"
    Then the bot should send:
      """
      Non hai inserito il giorno: scrivi /setday <giorno>
      """
    And the bot should send nothing else
    And the match should have:
      | field | value                |
      | day   | Mercoledì 28/10/2026 |

  Scenario: /setday with a readable date schedules the payment reminder
    Given a match was started
    When "@mario" sends "/setday 25/10/2026"
    Then the bot should send:
      """
      Ok, @mario! Ho impostato il giorno della partita il 25/10/2026
      """
    And the bot should send:
      """
      *GIORNO*: 25/10/2026 | 20:00

      {ten empty slots}

      {default tail}
      """
    And the bot should pin the summary
    When the scheduled jobs run
    Then the bot should send plain text:
      """
      {payment reminder}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  Scenario: /setday replaces the previous payment reminder instead of adding another one
    Given a match was started
    And "@mario" had sent "/setday 25/10/2026"
    And "@mario" had sent "/setday 26/10/2026"
    When the scheduled jobs run
    Then the bot should send plain text:
      """
      {payment reminder}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  Scenario: /setday with free text cancels the previous payment reminder
    Given a match was started
    And "@mario" had sent "/setday 25/10/2026"
    And "@mario" had sent "/setday sabato"
    When the scheduled jobs run
    Then the bot should send nothing else

  Scenario: /setday with a date in the past schedules no payment reminder
    Given a match was started
    When "@mario" sends "/setday 20/10/2026"
    Then the bot should send:
      """
      Ok, @mario! Ho impostato il giorno della partita il 20/10/2026
      """
    And the bot should send:
      """
      *GIORNO*: 20/10/2026 | 20:00

      {ten empty slots}

      {default tail}
      """
    And the bot should pin the summary
    When the scheduled jobs run
    Then the bot should send nothing else

  @known-bug @issue-8
  Scenario: The day written by the bot itself cannot be read back, so no payment reminder is ever scheduled
    Given a match was started
    When "@mario" sends "/settime 21:00"
    Then the bot should send:
      """
      Ok, @mario! Ho impostato l'orario della partita alle 21:00
      """
    And the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 21:00

      {ten empty slots}

      {default tail}
      """
    And the bot should pin the summary
    When the scheduled jobs run
    Then the bot should send nothing else

  @known-bug @issue-91
  Scenario: The payment reminder replaces the summary as the message edited by later changes
    Given a match was started
    And "@mario" had sent "/setday 25/10/2026"
    When the scheduled jobs run
    Then the bot should send plain text:
      """
      {payment reminder}
      """
    And the bot should pin the last message
    And the match summary message should be the last message of the bot
    When "@mario" sends "/setpitch Crespi"
    Then the bot should send:
      """
      Ok, @mario! Ho aggiornato il campo!
      """
    And the bot should edit the summary to:
      """
      *GIORNO*: 25/10/2026 | 20:00

      {ten empty slots}

      {default description}

      *CAMPO*: 
      Crespi
      """
    And the bot should pin the summary
    And the bot should send nothing else

  # ---- /settime --------------------------------------------------------------------------------

  Scenario: /settime with a valid time confirms, then sends and pins the summary
    Given a match was started
    When "@mario" sends "/settime 21:30"
    Then the bot should send:
      """
      Ok, @mario! Ho impostato l'orario della partita alle 21:30
      """
    And the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 21:30

      {ten empty slots}

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match should have:
      | field | value                |
      | day   | Mercoledì 28/10/2026 |
      | time  | 21:30                |

  Scenario: /settime schedules the payment reminder when the day is readable
    Given a match was started
    And "@mario" had sent "/setday 25/10/2026"
    When "@mario" sends "/settime 21:30"
    Then the bot should send:
      """
      Ok, @mario! Ho impostato l'orario della partita alle 21:30
      """
    And the bot should edit the summary to:
      """
      *GIORNO*: 25/10/2026 | 21:30

      {ten empty slots}

      {default tail}
      """
    And the bot should pin the summary
    When the scheduled jobs run
    Then the bot should send plain text:
      """
      {payment reminder}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  Scenario: /settime replaces the previous payment reminder instead of adding another one
    Given a match was started
    And "@mario" had sent "/setday 25/10/2026"
    And "@mario" had sent "/settime 21:30"
    And "@mario" had sent "/settime 22:30"
    When the scheduled jobs run
    Then the bot should send plain text:
      """
      {payment reminder}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  @known-bug @issue-92
  Scenario Outline: /settime does not validate the time: "<text>" is stored as it is
    Given a match was started
    And "@mario" had sent "/setday 25/10/2026"
    When "@mario" sends "/settime <text>"
    Then the bot should send:
      """
      Ok, @mario! Ho impostato l'orario della partita alle <text>
      """
    And the bot should edit the summary to:
      """
      *GIORNO*: 25/10/2026 | <text>

      {ten empty slots}

      {default tail}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match should have:
      | field | value  |
      | time  | <text> |

    Examples:
      | text      |
      | 25:99     |
      | stasera   |
      | alle 21   |
      | 9:30      |

  Scenario: /settime with an unreadable time still schedules the payment reminder from the day
    Given a match was started
    And "@mario" had sent "/setday 25/10/2026"
    And "@mario" had sent "/settime stasera"
    When the scheduled jobs run
    Then the bot should send plain text:
      """
      {payment reminder}
      """
    And the bot should pin the last message
    And the bot should send nothing else

  Scenario: /settime without argument explains the usage
    Given a match was started
    When "@mario" sends "/settime"
    Then the bot should send:
      """
      Non hai inserito l'orario: scrivi /settime <orario>
      """
    And the bot should send nothing else
    And the match should have:
      | field | value |
      | time  | 20:00 |

  # ---- /setpitch -------------------------------------------------------------------------------

  Scenario: /setpitch sets the pitch, confirms, then sends and pins the summary
    Given a match was started
    When "@mario" sends "/setpitch Crespi Sport Village"
    Then the bot should send:
      """
      Ok, @mario! Ho aggiornato il campo!
      """
    And the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      {ten empty slots}

      {default description}

      *CAMPO*: 
      Crespi Sport Village
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match pitch should be:
      """
      Crespi Sport Village
      """

  Scenario: /setpitch again edits the summary
    Given a match was started
    And "@mario" had sent "/setpitch Crespi"
    When "@mario" sends "/setpitch Campo   di   quartiere"
    Then the bot should send:
      """
      Ok, @mario! Ho aggiornato il campo!
      """
    And the bot should edit the summary to:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      {ten empty slots}

      {default description}

      *CAMPO*: 
      Campo di quartiere
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match pitch should be:
      """
      Campo di quartiere
      """

  Scenario: /setpitch escapes Markdown characters in the summary and the sender name
    Given a match was started
    And the user "@mario_rossi"
    When "@mario_rossi" sends "/setpitch campo_1"
    Then the bot should send:
      """
      Ok, @mario\_rossi! Ho aggiornato il campo!
      """
    And the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      {ten empty slots}

      {default description}

      *CAMPO*: 
      campo\_1
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match pitch should be:
      """
      campo_1
      """

  Scenario: The sender name is shown lowercase
    Given a match was started
    And the user "@MarioRossi"
    When "@MarioRossi" sends "/setpitch Crespi"
    Then the bot should send:
      """
      Ok, @mariorossi! Ho aggiornato il campo!
      """
    And the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      {ten empty slots}

      {default description}

      *CAMPO*: 
      Crespi
      """
    And the bot should pin the summary
    And the bot should send nothing else

  Scenario: /setpitch without argument explains the usage
    Given a match was started
    When "@mario" sends "/setpitch"
    Then the bot should send:
      """
      Non hai inserito il campo: scrivi /setpitch <campo>
      """
    And the bot should send nothing else
    And the match should have:
      | field | value  |
      | pitch | (none) |

  # ---- /setdescription -------------------------------------------------------------------------

  Scenario: /setdescription replaces the default description, confirms, then sends and pins the summary
    Given a match was started
    When "@mario" sends "/setdescription Partita di coppa, portate la maglia"
    Then the bot should send:
      """
      Ok, @mario! Ho aggiornato la descrizione!
      """
    And the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      {ten empty slots}

      Partita di coppa, portate la maglia


      *CAMPO*: 
      {pitch hint}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match description should be:
      """
      Partita di coppa, portate la maglia

      """

  Scenario: /setdescription keeps Markdown formatting in the summary
    Given a match was started
    When "@mario" sends "/setdescription Portare *due* maglie"
    Then the bot should send:
      """
      Ok, @mario! Ho aggiornato la descrizione!
      """
    And the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      {ten empty slots}

      Portare *due* maglie


      *CAMPO*: 
      {pitch hint}
      """
    And the bot should pin the summary
    And the bot should send nothing else

  @known-bug @issue-99
  Scenario: /setdescription on several lines collapses them into a single line
    Given a match was started
    When "@mario" sends the message:
      """
      /setdescription Prima riga
      seconda riga

      terza   riga
      """
    Then the bot should send:
      """
      Ok, @mario! Ho aggiornato la descrizione!
      """
    And the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      {ten empty slots}

      Prima riga seconda riga terza riga


      *CAMPO*: 
      {pitch hint}
      """
    And the bot should pin the summary
    And the bot should send nothing else
    And the match description should be:
      """
      Prima riga seconda riga terza riga

      """

  Scenario: /setdescription again edits the summary
    Given a match was started
    And "@mario" had sent "/setdescription Prima"
    When "@mario" sends "/setdescription Seconda"
    Then the bot should send:
      """
      Ok, @mario! Ho aggiornato la descrizione!
      """
    And the bot should edit the summary to:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      {ten empty slots}

      Seconda


      *CAMPO*: 
      {pitch hint}
      """
    And the bot should pin the summary
    And the bot should send nothing else

  Scenario: /setdescription without argument explains the usage
    Given a match was started
    When "@mario" sends "/setdescription"
    Then the bot should send:
      """
      Non hai inserito la descrizione: scrivi /setdescription <descrizione>
      """
    And the bot should send nothing else
    And the match description should be:
      """
      {default description}
      """

  # ---- the summary when the bot cannot pin -----------------------------------------------------

  Scenario: Changes still work when the bot cannot pin the summary
    Given a match was started
    And the bot is not an administrator of the chat
    When "@mario" sends "/setpitch Crespi"
    Then the bot should send:
      """
      Ok, @mario! Ho aggiornato il campo!
      """
    And the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      {ten empty slots}

      {default description}

      *CAMPO*: 
      Crespi
      """
    And the bot should pin the summary
    And the bot should send nothing else

  # ---- users without a username ----------------------------------------------------------------

  @known-bug @issue-88
  Scenario: /setnumber from a user without username claims the number is missing
    Given a match was started
    And a user named "Luca" without username
    When "Luca" sends "/setnumber 4"
    Then the bot should send:
      """
      Non hai inserito il numero: scrivi /setnumber <numero>
      """
    And the bot should send nothing else
    And the match should have:
      | field  | value |
      | target | 10    |

  @known-bug @issue-88
  Scenario Outline: <command> from a user without username saves the change and then crashes without answering
    Given a match was started
    And a user named "Luca" without username
    And the bot is expected to crash on the next message
    When "Luca" sends "<command>"
    Then the bot should fail with "AttributeError"
    And the bot should send nothing else
    And the match should have:
      | field   | value   |
      | <field> | <value> |

    Examples:
      | command                     | field       | value      |
      | /setday 25/10/2026          | day         | 25/10/2026 |
      | /settime 21:30              | time        | 21:30      |
      | /setpitch Crespi            | pitch       | Crespi     |

  # ---- default day ----------------------------------------------------------------------------

  Scenario Outline: /start on <now> picks <day>
    Given the clock moves to "<now>"
    When "@mario" sends "/start"
    Then the bot should send the text "welcome"
    And the bot should send nothing else
    And the match should have:
      | field | value |
      | day   | <day> |

    Examples:
      | now              | day                  |
      | 2026-10-19 09:00 | Mercoledì 21/10/2026 |
      | 2026-10-20 23:59 | Mercoledì 21/10/2026 |
      | 2026-10-22 09:00 | Mercoledì 28/10/2026 |
      | 2026-10-25 12:00 | Mercoledì 28/10/2026 |
      | 2026-12-30 18:00 | Mercoledì 06/01/2027 |

  @known-bug @issue-34
  Scenario Outline: /start on a Wednesday at <time> skips to the following Wednesday, even before the match could happen
    Given the clock moves to "2026-10-21 <time>"
    When "@mario" sends "/start"
    Then the bot should send the text "welcome"
    And the bot should send nothing else
    And the match should have:
      | field | value                |
      | day   | Mercoledì 28/10/2026 |

    Examples:
      | time  |
      | 00:01 |
      | 08:00 |
      | 19:59 |
      | 23:59 |

  Scenario: The default day is computed once, when the match is started
    Given a match was started
    And the clock moves to "2026-10-30 12:00"
    When "@mario" sends "/setpitch Crespi"
    Then the bot should send:
      """
      Ok, @mario! Ho aggiornato il campo!
      """
    And the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 20:00

      {ten empty slots}

      {default description}

      *CAMPO*: 
      Crespi
      """
    And the bot should pin the summary
    And the bot should send nothing else
