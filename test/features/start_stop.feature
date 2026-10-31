Feature: Starting and stopping a match
  A group chat has at most one match. /start creates it, /stop removes it,
  and every other command refuses to work until a match has been started.

  Background:
    Given a group chat "Calcetto"
    And the user "@mario"
    And today is "2026-10-21 21:00"
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
    And the text "default description" is:
      """
      5 goal di scarto e le squadre si _potrebbero_ cambiare 
      6 goal di scarto e le squadre si *devono* cambiare 
      (ditelo a chiunque invitate) 
      *PORTARE UNA MAGLIA BIANCA E UNA COLORATA*

      """

  Scenario: /start on a chat without a match creates one with the defaults
    When "@mario" sends "/start"
    Then the bot should send the text "welcome"
    And the bot should send nothing else
    And the match should have:
      | field   | value                |
      | players | (none)               |
      | target  | 10                   |
      | day     | Mercoledì 28/10/2026 |
      | time    | 20:00                |
      | pitch   | (none)               |
      | teams   | (none)               |
    And the match description should be:
      """
      {default description}
      """

  Scenario: /start from a user without username works the same
    Given a user named "Luca" without username
    When "Luca" sends "/start"
    Then the bot should send the text "welcome"
    And the bot should send nothing else
    And the match should have:
      | field   | value                |
      | players | (none)               |
      | target  | 10                   |

  Scenario: /start when a match already exists keeps the match untouched
    Given a match was started
    When "@mario" sends "/settime 21:30"
    Then the bot should send:
      """
      Ok, @mario! Ho impostato l'orario della partita alle 21:30
      """
    And the bot should send:
      """
      *GIORNO*: Mercoledì 28/10/2026 | 21:30

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

      {default description}

      *CAMPO*: 
      Usa il comando /setpitch <campo> per inserire la struttura sportiva dove giocherete.
      """
    And the bot should pin the last message
    When "@mario" sends "/start"
    Then the bot should send the text "welcome"
    And the bot should send nothing else
    And the match should have:
      | field | value |
      | time  | 21:30 |

  @issue-25
  Scenario: An edited /start is ignored and does not create a match
    When "@mario" edits a message into "/start"
    Then the bot should send nothing else
    And there should be no match for this chat

  @issue-25
  Scenario Outline: An edited <command> is ignored and leaves the match untouched
    Given a match was started
    When "@mario" edits a message into "<command>"
    Then the bot should send nothing else
    And the match should have:
      | field  | value |
      | target | 10    |

    Examples:
      | command       |
      | /setnumber 4  |
      | /participants |
      | /stop         |

  Scenario: /stop removes the match
    Given a match was started
    When "@mario" sends "/stop"
    Then the bot should send:
      """
      Ho cancellato la partita.
      """
    And the bot should send nothing else
    And there should be no match for this chat

  Scenario: /stop only removes the match of its own chat
    Given a match was started
    And a group chat "Altra squadra"
    When "@mario" sends "/start" in "Altra squadra"
    Then the bot should send the text "welcome"
    When "@mario" sends "/stop" in "Altra squadra"
    Then the bot should send:
      """
      Ho cancellato la partita.
      """
    And there should be no match for this chat
    And there should be a match for "Calcetto"

  Scenario: /stop without a match explains how to start one
    When "@mario" sends "/stop"
    Then the bot should send:
      """
      Prima di iniziare con le danze, avvia una partita, per farlo usa /start
      """
    And the bot should send nothing else
    And there should be no match for this chat

  Scenario: /start again after /stop begins from the defaults
    Given a match was started
    When "@mario" sends "/stop"
    Then the bot should send:
      """
      Ho cancellato la partita.
      """
    When "@mario" sends "/start"
    Then the bot should send the text "welcome"
    And the match should have:
      | field | value                |
      | day   | Mercoledì 28/10/2026 |

  Scenario: /help lists all the commands, even without a match
    When "@mario" sends "/help"
    Then the bot should send:
      """
      Ecco a te la lista completa dei comandi di questo bot: 
      - se sei in forse scrivi _proponimi_, 
      - se vuoi proporre qualcuno scrivi _proponi <nome>_, 
      - per essere aggiunto o confermato rispondi _aggiungimi_,
      - per aggiungere o confermare qualcuno usa _aggiungi <nome>_,
      - per essere rimosso _toglimi_, 
      - per rimuovere qualcuno _togli <nome>_, 
      - per modificare le squadre scrivi _scambia <nome 1> con <nome 2>_. 

      Posso anche pinnare i messaggi se vuoi ma per farlo ricordati di aggiungermi come amministratore.

      /start - Crea una nuova partita 
      /setnumber - Imposta il numero di partecipanti 
      /setday - Imposta il giorno della partita 
      /settime - Imposta l’orario della partita 
      /setdescription - Imposta la descrizione sotto i partecipanti 
      /setpitch - Imposta il campo 
      /participants - Mostra i partecipanti della partita attuale 
      /teams - Mostra le squadre della partita attuale 
      /stop - Rimuovi la partita 
      /help - Mostra la lista di comandi disponibili
      """
    And the bot should send nothing else
    And there should be no match for this chat

  Scenario: /participants before /start is refused and does not create a match
    When "@mario" sends "/participants"
    Then the bot should send:
      """
      Prima di iniziare con le danze, avvia una partita, per farlo usa /start
      """
    And the bot should send nothing else
    And there should be no match for this chat

  Scenario: /participants right after /start shows the empty summary and pins it
    Given a match was started
    When "@mario" sends "/participants"
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

      {default description}

      *CAMPO*: 
      Usa il comando /setpitch <campo> per inserire la struttura sportiva dove giocherete.
      """
    And the bot should pin the last message
    And the bot should send nothing else

  Scenario: /start in a chat with a default pitch gives the match that pitch
    Given the chat has the default pitch "Campo Rossi"
    When "@mario" sends "/start"
    Then the bot should send the text "welcome"
    And the bot should send nothing else
    When "@mario" sends "/participants"
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

      {default description}

      *CAMPO*: 
      Campo Rossi
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field | value       |
      | pitch | Campo Rossi |

  Scenario: /bamboo in a chat with another default pitch keeps the bamboo pitch
    Given the chat has the default pitch "Campo Rossi"
    When "@mario" sends "/bamboo"
    Then the bot should send the text "welcome"
    And the bot should send nothing else
    When "@mario" sends "/participants"
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

      {default description}

      *CAMPO*: 
      Crespi Sport Village 

      Via Carlo Valvassori Peroni, 48, 20133 
      Milano, MI, 02 266 3774 
      https://g.co/kgs/L9b6KZ
      """
    And the bot should pin the last message
    And the bot should send nothing else
    And the match should have:
      | field | value                                                                                                                      |
      | pitch | Crespi Sport Village \n\nVia Carlo Valvassori Peroni, 48, 20133 \nMilano, MI, 02 266 3774 \nhttps://g.co/kgs/L9b6KZ |
