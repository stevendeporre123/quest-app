import xml.etree.ElementTree as ET
from typing import Tuple
import re
from html import unescape


def _clean_html(raw: str) -> str:
    """Convert stored HTML-ish fragments into plain text."""
    if not raw:
        return ""
    text = raw.replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r"</p\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p\s*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = unescape(text.replace("&nbsp;", " "))
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def parse_agenda_xml(xml_str: str):
    """Parse the Agenda.xml and return (oralQuestions, meeting_date, commission_name)."""
    root = ET.fromstring(xml_str)

    def first_text(xpath: str) -> str:
        el = root.find(xpath)
        return (el.text or "").strip() if el is not None and el.text else ""

    meeting_date = ""
    commission_name = ""

    start_date = first_text(".//startDateAsDate")
    if start_date:
        meeting_date = start_date.split("T")[0]
    else:
        meeting_dt = first_text(".//meetingDate")
        if meeting_dt:
            meeting_date = meeting_dt.split("T")[0]

    organ_name = first_text(".//organ/name")
    if organ_name:
        commission_name = organ_name
    else:
        # fallback to previous behaviour
        meeting_name = first_text(".//meetingItem/name")
        if meeting_name:
            commission_name = meeting_name

    oral_questions = []

    for roi in root.iter():
        tag = roi.tag.split("}", 1)[-1]
        if tag != "roiDetail":
            continue

        def txt(name: str) -> str:
            el = roi.find(name)
            return (el.text or "").strip() if el is not None and el.text else ""

        custom_fields = {}
        custom_el = roi.find("custom")
        if custom_el is not None:
            for field in custom_el.findall("field"):
                key = field.get("key")
                if key:
                    custom_fields[key] = (field.text or "").strip()

        def custom_or_tag(name: str) -> str:
            return txt(name) or custom_fields.get(name, "")

        roi_type = (txt("roitype") or txt("roiType")).upper()
        if "ORALQUESTION" not in roi_type:
            continue

        title   = txt("title")
        subject = txt("subject")
        rid     = txt("id")
        year_nr = txt("yearNr")
        seq_nr  = txt("sequenceNr")

        context_html = custom_or_tag("toelichting_context_text")
        vraag_html = custom_or_tag("basisgegevens_vraagstelling_text")
        context_text = _clean_html(context_html)
        vraag_text = _clean_html(vraag_html)
        combined_question = "\n\n".join(
            part for part in (context_text, vraag_text) if part
        )

        # submitter
        submitter = {"givenName": "", "familyName": "", "faction": ""}
        submitters_el = roi.find("submitters")
        if submitters_el is not None:
            s = submitters_el.find("submitter")
            if s is not None:
                given = s.findtext("givenName") or ""
                family = s.findtext("familyName") or ""
                fact_name = ""
                f_el = s.find("faction/name")
                if f_el is not None and f_el.text:
                    fact_name = f_el.text.strip()
                submitter = {
                    "givenName": given.strip(),
                    "familyName": family.strip(),
                    "faction": fact_name,
                }

        # assignee
        assignee = {"label": "", "givenName": "", "familyName": ""}
        assignees_el = roi.find("assignees")
        if assignees_el is not None:
            a = assignees_el.find("assignee")
            if a is not None:
                given = (a.findtext("givenName") or "").strip()
                family = (a.findtext("familyName") or "").strip()
                title_node = (a.findtext("title") or "").strip()
                parts = []
                if title_node:
                    parts.append(title_node)
                if given:
                    parts.append(given)
                if family:
                    parts.append(family)
                assignee = {
                    "label": " ".join(parts),
                    "givenName": given,
                    "familyName": family,
                }

        oral_questions.append({
            "meeting_date": meeting_date,
            "commission_name": commission_name,
            "dossier_id": rid,
            "dossier_year_nr": year_nr,
            "sequence_nr": seq_nr,
            "title": title,
            "subject": subject,
            "roi_type": roi_type,
            "submitter_given_name": submitter["givenName"],
            "submitter_family_name": submitter["familyName"],
            "submitter_faction": submitter["faction"],
            "assignee_label": assignee["label"],
            "assignee_given_name": assignee["givenName"],
            "assignee_family_name": assignee["familyName"],
            "question_context_from_xml": context_text,
            "question_body_from_xml": vraag_text,
            "question_text_from_xml": combined_question,
        })

    return oral_questions, meeting_date, commission_name
