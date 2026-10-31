@payment-reminder
Feature: Payment reminder
  When a match is fully booked, or when its day or time change, the bot schedules a reminder
  for the group: 2 hours after the match start, only if that moment is still in the future.
  When it fires it asks who has not paid yet and pins the message.
  A day or time the bot cannot understand is refused and leaves the match, and its reminder, as it was.

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
    And the text "campo" is:
      """
      *CAMPO*: 
      Usa il comando /setpitch <campo> per inserire la struttura sportiva dove giocherete.
      """
    And the text "empty slots" is:
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
    And the text "payment reminder" is:
      """
      Ciao bestie 😎, com'è andata la partita? C'è qualcuno che non ha ancora pagato la sua quota?
      """
    And the text "kickoff" is:
      """
      🚀 *SI GIOCA* 🚀 facciamo le squadre? /teams 😎
      """


  Scenario: /setday with a valid date schedules the reminder 2 hours after the default time
    Given a match was started
    When "@mario" sends "/setday 28/10/2026"
    Then the bot should send:
          """
          Ok, @mario! Ho impostato il giorno della partita: mercoledì 28/10/2026
          """
    And the bot should send:
          """
          *GIORNO*: Mercoledì 28/10/2026 | 20:00
    
          {empty slots}
    
          {default description}
    
          {campo}
          """
    And the bot should pin the last message
    And a payment reminder should be scheduled for "2026-10-28 22:00"
    And the bot should send nothing else
    And the match should have:
      | field | value      |
      | day   | Mercoledì 28/10/2026 |
      | time  | 20:00      |

  Scenario: /settime with a valid time moves the reminder 2 hours after the new time
    Given a match was started
    And "@mario" had sent "/setday 29/10/2026"
    When "@mario" sends "/settime 21:30"
    Then the bot should send:
          """
          Ok, @mario! Ho impostato l'orario della partita alle 21:30
          """
    And the bot should edit the summary to:
          """
          *GIORNO*: Giovedì 29/10/2026 | 21:30
    
          {empty slots}
    
          {default description}
    
          {campo}
          """
    And the bot should pin the summary
    And a payment reminder should be scheduled for "2026-10-29 23:30"
    And the bot should send nothing else

  Scenario: /settime with a time written with a dot is normalised and schedules the reminder 2 hours after it
    Given a match was started
    And "@mario" had sent "/setday 27/10/2026"
    When "@mario" sends "/settime 21.30"
    Then the bot should send:
          """
          Ok, @mario! Ho impostato l'orario della partita alle 21:30
          """
    And the bot should edit the summary to:
          """
          *GIORNO*: Martedì 27/10/2026 | 21:30
    
          {empty slots}
    
          {default description}
    
          {campo}
          """
    And the bot should pin the summary
    And a payment reminder should be scheduled for "2026-10-27 23:30"
    And the bot should send nothing else

  Scenario: /settime with the default day schedules the reminder 2 hours after the new time
    Given a match was started
    When "@mario" sends "/settime 21:30"
    Then the bot should send:
          """
          Ok, @mario! Ho impostato l'orario della partita alle 21:30
          """
    And the bot should send:
          """
          *GIORNO*: Mercoledì 28/10/2026 | 21:30
    
          {empty slots}
    
          {default description}
    
          {campo}
          """
    And the bot should pin the last message
    And a payment reminder should be scheduled for "2026-10-28 23:30"
    And the bot should send nothing else

  Scenario: Reaching the target with the default day schedules the reminder 2 hours after the default time
    Given a match was started
    And "@mario" had sent "/setnumber 2"
    And "@mario" had sent "aggiungi anna"
    When "@mario" sends "aggiungi bruno"
    Then the bot should send:
          """
          Ok, aggiungo bruno
          """
    And the bot should edit the summary to:
          """
          *GIORNO*: Mercoledì 28/10/2026 | 20:00
    
          1. anna ✅
          2. bruno ✅
    
          {default description}
    
          {campo}
          """
    And the bot should pin the summary
    And the bot should send the text "kickoff"
    And a payment reminder should be scheduled for "2026-10-28 22:00"
    And the bot should send nothing else

  Scenario: Starting on a Wednesday before the match time makes today the default day, with its reminder
    Given the clock moves to "2026-10-21 19:00"
    And a match was started
    When "@mario" sends "/settime 21:00"
    Then the bot should send:
          """
          Ok, @mario! Ho impostato l'orario della partita alle 21:00
          """
    And the bot should send:
          """
          *GIORNO*: Mercoledì 21/10/2026 | 21:00
    
          {empty slots}
    
          {default description}
    
          {campo}
          """
    And the bot should pin the last message
    And a payment reminder should be scheduled for "2026-10-21 23:00"
    And the bot should send nothing else

  Scenario: /setday with a date in the past schedules no reminder
    Given a match was started
    When "@mario" sends "/setday 20/10/2026"
    Then the bot should send:
          """
          Ok, @mario! Ho impostato il giorno della partita: martedì 20/10/2026
          """
    And the bot should send:
          """
          *GIORNO*: Martedì 20/10/2026 | 20:00
    
          {empty slots}
    
          {default description}
    
          {campo}
          """
    And the bot should pin the last message
    And no payment reminder should be scheduled
    And the bot should send nothing else

  Scenario: /setday with today schedules the reminder while it is still in the future
    Given a match was started
    When "@mario" sends "/setday 21/10/2026"
    Then the bot should send:
          """
          Ok, @mario! Ho impostato il giorno della partita: mercoledì 21/10/2026
          """
    And the bot should send:
          """
          *GIORNO*: Mercoledì 21/10/2026 | 20:00
    
          {empty slots}
    
          {default description}
    
          {campo}
          """
    And the bot should pin the last message
    And a payment reminder should be scheduled for "2026-10-21 22:00"
    And the bot should send nothing else

  Scenario: /settime that moves the reminder into the past drops the previous one
    Given a match was started
    And "@mario" had sent "/setday 21/10/2026"
    Then a payment reminder should be scheduled for "2026-10-21 22:00"
    When "@mario" sends "/settime 15:00"
    Then the bot should send:
          """
          Ok, @mario! Ho impostato l'orario della partita alle 15:00
          """
    And the bot should edit the summary to:
          """
          *GIORNO*: Mercoledì 21/10/2026 | 15:00
    
          {empty slots}
    
          {default description}
    
          {campo}
          """
    And the bot should pin the summary
    And no payment reminder should be scheduled
    And the bot should send nothing else

  Scenario: /setday with something that is not a date keeps the previous reminder
    Given a match was started
    And "@mario" had sent "/setday 28/10/2026"
    Then a payment reminder should be scheduled for "2026-10-28 22:00"
    When "@mario" sends "/setday boh"
    Then the bot should send:
          """
          Non ho capito il giorno, @mario: scrivilo come GG/MM/AAAA, per esempio /setday 25/10/2026
          """
    And a payment reminder should be scheduled for "2026-10-28 22:00"
    And the bot should send nothing else

  Scenario: Changing the time replaces the previous reminder instead of adding another one
    Given a match was started
    And "@mario" had sent "/setday 28/10/2026"
    When "@mario" sends "/settime 21:30"
    Then the bot should send:
          """
          Ok, @mario! Ho impostato l'orario della partita alle 21:30
          """
    And the bot should edit the summary to:
          """
          *GIORNO*: Mercoledì 28/10/2026 | 21:30
    
          {empty slots}
    
          {default description}
    
          {campo}
          """
    And the bot should pin the summary
    And a payment reminder should be scheduled for "2026-10-28 23:30"
    And the bot should send nothing else

  Scenario: /setday without a match schedules nothing
    When "@mario" sends "/setday 28/10/2026"
    Then the bot should send:
          """
          Prima di iniziare con le danze, avvia una partita, per farlo usa /start
          """
    And no payment reminder should be scheduled
    And the bot should send nothing else

  Scenario: /setday without a day keeps the scheduled reminder
    Given a match was started
    And "@mario" had sent "/setday 28/10/2026"
    When "@mario" sends "/setday"
    Then the bot should send:
          """
          Non hai inserito il giorno: scrivi /setday <giorno>
          """
    And a payment reminder should be scheduled for "2026-10-28 22:00"
    And the bot should send nothing else

  Scenario: The reminder asks who has not paid, pins the message and becomes the match summary message
    Given a match was started
    And "@mario" had sent "/setday 28/10/2026"
    When the scheduled jobs run
    Then the bot should send the plain text "payment reminder"
    And the bot should pin the last message
    And the match summary message should be the last message of the bot
    And the bot should send nothing else

  # Documents current behaviour (not a bug: Telegram accepts both): the job uses `chat_id = job.name`,
  # a string, whereas handlers use the integer id. The other scenarios compare the chat id regardless of type.
  Scenario: The reminder job addresses the chat with its id as a string
    Given a match was started
    And "@mario" had sent "/setday 28/10/2026"
    When the scheduled jobs run
    Then the bot should send the plain text "payment reminder"
    And the last thing the bot did should address the chat with its id as a string
    And the bot should pin the last message
    And the last thing the bot did should address the chat with its id as a string
    And the bot should send nothing else

  Scenario: The reminder is sent even if the bot cannot pin it
    Given a match was started
    And "@mario" had sent "/setday 28/10/2026"
    And the bot is not an administrator of the chat
    When the scheduled jobs run
    Then the bot should send the plain text "payment reminder"
    And the bot should pin the last message
    And the bot should log the warning "No admin rights to pin the message"
    And the match summary message should be the last message of the bot
    And the bot should send nothing else

  @known-bug @issue-89
  Scenario: Reaching the target after /setday schedules a second reminder
    Given a match was started
    And "@mario" had sent "/setnumber 2"
    And "@mario" had sent "/setday 28/10/2026"
    And "@mario" had sent "aggiungi anna"
    When "@mario" sends "aggiungi bruno"
    Then the bot should send:
          """
          Ok, aggiungo bruno
          """
    And the bot should edit the summary to:
          """
          *GIORNO*: Mercoledì 28/10/2026 | 20:00
    
          1. anna ✅
          2. bruno ✅
    
          {default description}
    
          {campo}
          """
    And the bot should pin the summary
    And the bot should send the text "kickoff"
    And 2 payment reminders should be scheduled for "2026-10-28 22:00"
    And the bot should send nothing else

  @known-bug @issue-89
  Scenario: Reaching the target after /setday makes the reminder fire twice
    Given a match was started
    And "@mario" had sent "/setnumber 2"
    And "@mario" had sent "/setday 28/10/2026"
    And "@mario" had sent "aggiungi anna"
    When "@mario" sends "aggiungi bruno"
    Then the bot should send:
          """
          Ok, aggiungo bruno
          """
    And the bot should edit the summary to:
          """
          *GIORNO*: Mercoledì 28/10/2026 | 20:00
    
          1. anna ✅
          2. bruno ✅
    
          {default description}
    
          {campo}
          """
    And the bot should pin the summary
    And the bot should send the text "kickoff"
    And the bot should send nothing else
    When the scheduled jobs run
    Then the bot should send the plain text "payment reminder"
    And the bot should pin the last message
    And the bot should send the plain text "payment reminder"
    And the bot should pin the last message
    And the bot should send nothing else

  Scenario: Removing a player after the teams were formed cancels the reminder until the target is reached again
    Given a match was started
    And "@mario" had sent "/setnumber 2"
    And "@mario" had sent "/setday 28/10/2026"
    And "@mario" had sent "aggiungi anna"
    And "@mario" had sent "aggiungi bruno"
    And "@mario" had sent "/teams"
    When "@mario" sends "togli anna"
    Then the bot should send:
          """
          Che vergogna, anna
          """
    And the bot should send:
          """
          *SQUADRE ANNULLATE*
          """
    And the bot should edit the summary to:
          """
          *GIORNO*: Mercoledì 28/10/2026 | 20:00
    
          1. bruno ✅
          2. ❌
    
          {default description}
    
          {campo}
          """
    And the bot should pin the summary
    And no payment reminder should be scheduled
    And the bot should send nothing else
    When "@mario" sends "aggiungi anna"
    Then the bot should send:
          """
          Ok, aggiungo anna
          """
    And the bot should edit the summary to:
          """
          *GIORNO*: Mercoledì 28/10/2026 | 20:00
    
          1. bruno ✅
          2. anna ✅
    
          {default description}
    
          {campo}
          """
    And the bot should pin the summary
    And the bot should send the text "kickoff"
    And a payment reminder should be scheduled for "2026-10-28 22:00"
    And the bot should send nothing else

  @known-bug @issue-112
  Scenario: /setday on an incomplete list schedules a reminder for a match that may never be played
    Given a match was started
    And "@mario" had sent "/setnumber 2"
    And "@mario" had sent "aggiungi anna"
    When "@mario" sends "/setday 28/10/2026"
    Then the bot should send:
          """
          Ok, @mario! Ho impostato il giorno della partita: mercoledì 28/10/2026
          """
    And the bot should edit the summary to:
          """
          *GIORNO*: Mercoledì 28/10/2026 | 20:00
    
          1. anna ✅
          2. ❌
    
          {default description}
    
          {campo}
          """
    And the bot should pin the summary
    And a payment reminder should be scheduled for "2026-10-28 22:00"
    And the bot should send nothing else

  @known-bug @issue-112
  Scenario: /settime on an incomplete list schedules a reminder for a match that may never be played
    Given a match was started
    And "@mario" had sent "/setnumber 2"
    And "@mario" had sent "aggiungi anna"
    When "@mario" sends "/settime 21:30"
    Then the bot should send:
          """
          Ok, @mario! Ho impostato l'orario della partita alle 21:30
          """
    And the bot should edit the summary to:
          """
          *GIORNO*: Mercoledì 28/10/2026 | 21:30
    
          1. anna ✅
          2. ❌
    
          {default description}
    
          {campo}
          """
    And the bot should pin the summary
    And a payment reminder should be scheduled for "2026-10-28 23:30"
    And the bot should send nothing else

  @known-bug @issue-112
  Scenario: Removing a player before the teams are drawn keeps the reminder although the list is no longer complete
    Given a match was started
    And "@mario" had sent "/setnumber 2"
    And "@mario" had sent "aggiungi anna"
    And "@mario" had sent "aggiungi bruno"
    When "@mario" sends "togli anna"
    Then the bot should send:
          """
          Che vergogna, anna
          """
    And the bot should edit the summary to:
          """
          *GIORNO*: Mercoledì 28/10/2026 | 20:00
    
          1. bruno ✅
          2. ❌
    
          {default description}
    
          {campo}
          """
    And the bot should pin the summary
    And a payment reminder should be scheduled for "2026-10-28 22:00"
    And the bot should send nothing else

  @known-bug @issue-90
  Scenario: /stop does not cancel the reminder: it still fires for the deleted match
    Given a match was started
    And "@mario" had sent "/setday 28/10/2026"
    When "@mario" sends "/stop"
    Then the bot should send:
          """
          Ho cancellato la partita.
          """
    And a payment reminder should be scheduled for "2026-10-28 22:00"
    And the bot should send nothing else
    When the scheduled jobs run
    Then the bot should send the plain text "payment reminder"
    And the bot should pin the last message
    And there should be no match for this chat
    And the bot should send nothing else

  @known-bug @issue-91
  Scenario: After the reminder fired, the next summary update edits the pinned reminder message
    Given a match was started
    And "@mario" had sent "/setday 28/10/2026"
    When the scheduled jobs run
    Then the bot should send the plain text "payment reminder"
    And the bot should pin the last message
    And the bot should send nothing else
    When "@mario" sends "/settime 21:30"
    Then the bot should send:
          """
          Ok, @mario! Ho impostato l'orario della partita alle 21:30
          """
    And the bot should edit the summary to:
          """
          *GIORNO*: Mercoledì 28/10/2026 | 21:30
    
          {empty slots}
    
          {default description}
    
          {campo}
          """
    And the bot should pin the summary
    And a payment reminder should be scheduled for "2026-10-28 23:30"
    And the bot should send nothing else

  Scenario: Each chat has its own reminder
    Given a match was started
    And "@mario" had sent "/setday 28/10/2026"
    And a group chat "Altra squadra"
    And "@mario" had sent "/start" in "Altra squadra"
    And "@mario" had sent "/setday 29/10/2026" in "Altra squadra"
    Then a payment reminder should be scheduled for "2026-10-29 22:00"
    And the current chat is "Calcetto"
    And a payment reminder should be scheduled for "2026-10-28 22:00"
    When the scheduled jobs run
    Then the bot should send the plain text "payment reminder"
    And the bot should pin the last message
    And the current chat is "Altra squadra"
    And the bot should send the plain text "payment reminder"
    And the bot should pin the last message
    And the bot should send nothing else
