# Issue 001 — XML meteen wegschrijven als meeting + vragen

## Context
Momenteel worden vergaderingen en vragen pas in de database aangemaakt nadat de volledige AI-verwerking (alle vragen in één keer) is afgerond. Daardoor:

- verschijnt de nieuwe vergadering pas na een lange wachttijd,
- kunnen vragen niet tussentijds geraadpleegd worden,
- is er geen zicht op gedeeltelijke resultaten wanneer de AI-call faalt of onderbroken wordt.

## Doel
- Zodra een XML-agenda en transcript zijn geüpload moet meteen een meeting-record met alle ruwe vraaggegevens (zoals in de XML) worden aangemaakt.
- Elke vraag moet al zichtbaar/in de database staan met een **processing_state** die aangeeft dat de AI-verwerking nog moet gebeuren.
- Extra meta-info over de meeting (totaal aantal vragen, planning state …) moet opgeslagen worden zodat vervolgstappen daarop kunnen steunen.

## Uitwerking (high-level)
1. Breid het datamodel uit:
   - meetings: `processing_state`, `total_questions`, `processed_questions`, `processing_error`, tijdstempels.
   - questions: `processing_state`, `processing_error`, `source_question_idx`, tijdstempels.
2. Pas `/api/upload` aan:
   - Parse XML → creëer meeting + schrijf transcript/meta (zoals nu), maar **voor** enige AI-call.
   - Voeg telkens een question-record toe met waarden uit XML (zowel `question_text_xml` als `question_text_raw` = ruwe tekst).
   - Zet `processing_state='queued'` (of `pending`) zodat de queue uit issue 002 deze meteen kan oppikken.
3. Lever een snelle response: `{"status": "queued", "meeting_id": …, "questions": len}`.

## Acceptatiecriteria
- Na upload verschijnt de nieuwe vergadering meteen in `/api/meetings`.
- In `questions`-tabel bestaan records met ingevulde metadata uit XML, ondanks dat AI-verwerking nog niet liep.
- API-respons vermeldt dat verwerking gepland is i.p.v. “ok”.
- Geen regressies aan bestaande UI: meeting detailpagina moet alvast de ruwe vragen tonen met een statusindicator.
