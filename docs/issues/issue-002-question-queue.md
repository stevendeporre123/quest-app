# Issue 002 — Server-side verwerkingsqueue vraag-per-vraag

## Context
De huidige aanpak stuurt alle vragen in één request naar OpenAI. Dat zorgt voor:
- hoge kans op time-outs,
- moeilijkheden om de voortgang op te volgen,
- geen mogelijkheid voor de gebruiker om andere taken uit te voeren terwijl de verwerking loopt.

Met issue 001 staan vragen al in de database, maar er is nog geen mechanisme dat ze sequentieel verwerkt.

## Doel
- Introduceer een server-side queue die elke vraag afzonderlijk verwerkt en opslaat.
- Maak de status raadpleegbaar (per meeting en globaal), zodat het UI kan tonen hoeveel vragen nog wachten.
- Laat meerdere vragen “in behandeling” staan zonder de upload-endpoint te blokkeren.

## Uitwerking (high-level)
1. Achtergrondprocessor:
   - Python-thread of asyncio-task die jobs uit een persistente tabel/kolom oppikt.
   - Job = `(meeting_id, question_id, source_idx)`.
   - Bij start zet `processing_state='in_progress'`, na succes `processing_state='done'`, bij fout `processing_state='error'` + melding.
   - Houd `processing_attempts`, `processing_error`, `processing_started_at`, `processing_completed_at` bij.
2. Gebruik bestaande `align_questions_with_vtt`, maar voed die per vraag (lijstje van één item) en schrijf de resultaten terug in dezelfde question-row.
3. API-uitbreidingen:
   - `GET /api/processing/meetings/{meeting_id}` → counters (pending/in_progress/completed/errors).
   - `GET /api/processing/queue` → globale wachtrijinfo.
4. Front-end:
   - Uploadpagina moet na succesvolle upload een statuskaart tonen (bv. “4/12 vragen verwerkt”).
   - Meetingdetailpagina toont per vraag een badge (`Queued`, `Bezig`, `Klaar`, `Fout`).

## Acceptatiecriteria
- Upload-response blokkeert niet meer op AI-processing.
- In de database verschuiven vragen automatisch van `queued` → `in_progress` → `done`.
- Status-API’s geven consistente tellingen (geverifieerd met enkele scenario’s).
- UI toont voortgang zonder manuele refresh (periodieke polling is oké).
