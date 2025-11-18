# Issue 004 — Adhoc aansluitingen & spontane vragen registreren

## Context
Naast vooraf ingediende vragen kunnen raadsleden zich tijdens de zitting nog “aansluiten” of een onvoorziene vraag lanceren. Nu:
- is er geen plek om zulke interventies vast te leggen,
- verdwijnen ze uit het overzicht/verslag,
- kunnen ze niet aan de oorspronkelijke vraag gekoppeld worden.

## Doel
- Bied een manier om adhoc interventies vast te leggen en te koppelen aan de relevante vraag.
- Toon deze aansluitingen in de meetinginterface en in exports zodat het verloop correct gereconstrueerd wordt.
- Laat eventueel basisinfo mee verwerken (naam raadslid, fractie, korte omschrijving, tijdcodes).

## Uitwerking (high-level)
1. Datamodel:
   - Nieuwe tabel `question_followups` met velden: `question_id`, `type` (aansluiting / extra vraag), `speaker_given_name`, `speaker_family_name`, `faction`, `start_time`, `end_time`, `text`, `notes`.
   - API’s om follow-ups te creëren, updaten, verwijderen.
2. UI:
   - In de meetingpagina per vraag een subsectie “Aansluitingen”.
   - Formulier om snel een interventie toe te voegen (autocompletion met raadsleden).
3. Integratie met verwerking:
   - Bij AI-output kan (optioneel) vermeld worden dat er aansluitingen waren, maar hoofdantwoord blijft intact.
   - Exports (Docx) nemen follow-ups op na het hoofdantwoord.

## Acceptatiecriteria
- Gebruiker kan minstens één adhoc interventie toevoegen aan een vraag via UI.
- Data wordt permanent opgeslagen (CRUD-endpoints).
- Meetingdetail en export tonen de interventies onder de hoofdvraag.
