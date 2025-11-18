import json
from typing import List, Optional
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Client initialiseren – gebruikt automatisch OPENAI_API_KEY uit je omgeving
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """Je bent een assistent die VTT-transcripties van gemeenteraadscommissies
structureert in combinatie met XML-agenda-informatie.

Je krijgt:
- Een lijst mondelinge vragen uit de XML, met per vraag:
  - meeting_date
  - commission_name
  - dossier_id, dossier_year_nr, sequence_nr
  - title, subject, roi_type
  - submitter (naam, fractie)
  - assignee (bevoegde schepen; label + naam)
  - question_text_from_xml = officieel aangeleverde vraag
- Een lijst bekende raadsleden en schepenen (councillors) met naamvarianten.
- Een hiërarchische topic-taxonomie (met labels en synoniemen).
- De volledige VTT-transcriptie van de vergadering.

TAAK PER VRAAG:
1. Lokaliseer in de VTT waar de vraagsteller spreekt en bepaal question_start_time / question_end_time.
2. Lokaliseer in de VTT waar de bevoegde schepen antwoordt en bepaal answer_start_time / answer_end_time.
3. question_text_raw = exact dezelfde tekst als question_text_from_xml (niet samenvatten, niet wijzigen).
4a. answer_text_verbatim = quasi letterlijke weergave van het antwoord van de schepen:
    - Schrijf in correct Nederlands, met lichte contextuele correcties (namen, versprekingen).
    - Respecteer inhoud, volgorde en kernzinnen; voeg enkel noodzakelijke verduidelijkingen toe.
4b. answer_text_raw = gebalde, goed leesbare synthese van hetzelfde antwoord:
    - Neem alle inhoudelijke elementen, cijfers, toezeggingen en vervolgacties op.
    - Laat bijkomende vragen van andere raadsleden en replieken van de vraagsteller achterwege.
    - Gebruik de lijst met raadsleden/assignees om namen en aanspreektitels consistent te houden.
5. summary = max. 3 zinnen in het Nederlands.
6. actions = lijst met actiepunten (strings) of leeg wanneer er geen acties zijn.
7. topics = kies enkel labels uit de aangeleverde taxonomie. Gebruik synoniemen om de juiste labelnaam terug te geven. Als niets past, gebruik "Overig".
8. answer_status = altijd 'draft'.
9. followups = lijst van spontane tussenkomsten die plaatsvinden vóór het antwoord van de schepen afgerond is (of onmiddellijk nadien):
   {
     "type": "followup" | "question" | "remark",
     "speaker_given_name": "",
     "speaker_family_name": "",
     "speaker_faction": "",
     "start_time": "H:MM:SS.mmm",
     "end_time": "H:MM:SS.mmm",
     "text": "korte samenvatting",
     "note": ""
   }
10. related_question_keys = lijst van dossier_id's of sequence nummers die aanduiden welke vragen inhoudelijk gebundeld moeten worden. Zet de hoofdvraag (waar het antwoord werd gegeven) als eerste element.

OUTPUT:
Geef strikt geldig JSON met:
{
  "items": [
    {
      "meeting_date": "...",
      "commission_name": "...",
      "dossier_id": "...",
      "dossier_year_nr": "...",
      "sequence_nr": "...",
      "id": "...",
      "title": "...",
      "subject": "...",
      "roi_type": "...",
      "submitter_given_name": "...",
      "submitter_family_name": "...",
      "submitter_faction": "...",
      "assignee_label": "...",
      "assignee_given_name": "...",
      "assignee_family_name": "...",
      "question_start_time": "H:MM:SS.mmm",
      "question_end_time": "H:MM:SS.mmm",
      "answer_start_time": "H:MM:SS.mmm",
      "answer_end_time": "H:MM:SS.mmm",
      "question_text_raw": "...",
      "answer_text_verbatim": "...",
      "answer_text_raw": "...",
      "summary": "max. 3 zinnen in het Nederlands",
      "actions": ["...", "..."],
      "topics": ["...", "..."],
      "answer_status": "draft",
      "note": "",
      "followups": [],
      "related_question_keys": []
    }
  ]
}

Als je een vraag in de VTT niet met voldoende zekerheid kan lokaliseren:
- Laat meeting_date/commission/dossier en alle metadata staan zoals aangeleverd.
- Zet question_text_raw, answer_text_verbatim en answer_text_raw op een lege string.
- Vul 'note' met bv. "Kon deze vraag niet met zekerheid in de transcriptie lokaliseren."
"""


def align_questions_with_vtt(
    questions: List[dict],
    vtt_text: str,
    councillors: Optional[List[dict]] = None,
    taxonomy: Optional[List[dict]] = None,
) -> list:
    """Stuur alle vragen + volledige VTT naar OpenAI en retourneer items-lijst."""

    if not client.api_key:
        raise RuntimeError(
            "OpenAI API key is niet ingesteld. "
            "Zet OPENAI_API_KEY in de omgeving."
        )

    councillor_json = json.dumps(councillors or [], ensure_ascii=False, indent=2)
    taxonomy_json = json.dumps(taxonomy or [], ensure_ascii=False, indent=2)

    user_content = (
        "XML-afgeleide vragen (JSON):\n\n"
        + json.dumps(questions, ensure_ascii=False, indent=2)
        + "\n\nBekende raadsleden en schepenen (JSON):\n\n"
        + councillor_json
        + "\n\nBeschikbare topic-taxonomie (JSON):\n\n"
        + taxonomy_json
        + "\n\nVolledige VTT-transcriptie:\n\n"
        + vtt_text
    )

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
    )

    # In de nieuwe client zit de content hier:
    content = resp.choices[0].message.content
    data = json.loads(content)
    items = data.get("items", [])

    lookup = {
        (q.get("dossier_id") or f"idx-{idx}"): q.get("question_text_from_xml", "")
        for idx, q in enumerate(questions)
    }
    for idx, item in enumerate(items):
        key = item.get("dossier_id") or f"idx-{idx}"
        item["question_text_raw"] = lookup.get(key, item.get("question_text_raw", ""))
        item.setdefault("answer_text_verbatim", item.get("answer_text_raw", ""))
        item.setdefault("answer_text_raw", "")
        item.setdefault("answer_status", "draft")
        item.setdefault("followups", [])
        item.setdefault("related_question_keys", [])

    return items
