# Issue 003 — Meervoudige vraagstellers met één antwoord

## Context
Tijdens commissies komt het vaak voor dat meerdere raadsleden vragen indienen over hetzelfde onderwerp. De voorzitter kondigt dat aan, waarna alle vraagstellers eerst aan bod komen, gevolgd door één gebundeld antwoord van de bevoegde schepen. Momenteel behandelt Quest elke vraag volledig apart, waardoor:
- antwoorden dubbel worden uitgeschreven,
- er geen referentie is naar het “moederantwoord”,
- redacteurs manueel moeten bijhouden dat vragen gekoppeld waren.

## Doel
- Laat vragen binnen dezelfde vergadering groeperen onder één “thread”.
- Duid aan welke vraag de primaire (eerste) is; volgende vragen erven het antwoord of verwijzen ernaar.
- Zorg dat de UI en export duidelijk aangeven dat vragen samengevoegd zijn.

## Uitwerking (high-level)
1. Datamodel:
   - Nieuwe tabel `question_groups` of extra velden op `questions`:
     - `group_slug` / `group_label`.
     - `group_primary_question_id`.
     - `inherits_answer_from_id` (optioneel).
   - Automatische defaults: elke vraag start in een eigen groep.
2. API’s:
   - Endpoint om een groep te creëren en leden toe te wijzen (bv. PATCH op `/api/questions/{id}/group`).
   - Mogelijkheid om tijdens upload te detecteren (via XML) of dossier_id’s samenvallen en automatisch een groep voor te stellen.
3. Verwerking:
   - Wanneer een vraag `inherits_answer_from_id` heeft, wordt bij AI-schrijfstap `answer_text_raw` gevuld als “Zie antwoord bij vraag X …” tenzij er handmatige overschrijving is.
   - Meetingdetail toont groep + link naar leidende vraag.
4. UI:
   - Selectie in meetingpagina om vragen te bundelen (multi-select of “Koppel aan vorige”).
   - Badge of label “Gekoppeld aan vraag #12”.

## Acceptatiecriteria
- Beheerder kan minstens via UI twee vragen aan dezelfde groep toewijzen.
- Gekoppelde vragen tonen een verwijzing naar het antwoord van de primaire vraag.
- In exports/overzichten is duidelijk dat één antwoord meerdere vragen afdekt.
