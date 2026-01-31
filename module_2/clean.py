"""
clean.py

Load applicant_data.json, normalize fields (numbers, blanks, dates), and write cleaned_applicant_data.json.
"""

import json
import re
from typing import Any


## ============================================================
## Configuration: input and output file locations
## ============================================================

INPUT_JSON = "applicant_data.json"
OUTPUT_JSON = "cleaned_applicant_data.json"


## ============================================================
## Helpers: normalize blank strings and parse numeric fields
## ============================================================

def blank_to_none(value: Any) -> Any:
    """
    Convert empty strings (or whitespace-only strings) to None; leave everything else unchanged.
    """
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def to_int(value: Any) -> int | None:
    """
    Convert a value to int when possible; return None if it is missing or invalid.
    """
    value = blank_to_none(value)
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def to_float(value: Any) -> float | None:
    """
    Convert a value to float when possible; return None if it is missing or invalid.
    """
    value = blank_to_none(value)
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


## ============================================================
## Helpers: clean decision and notification text into consistent formats
## ============================================================

def normalize_decision(decision: Any) -> str | None:
    """
    Normalize decision strings into a consistent capitalization (e.g., Accepted, Rejected, Interview).
    """
    decision = blank_to_none(decision)
    if decision is None:
        return None
    d = str(decision).strip().lower()

    mapping = {
        "accepted": "Accepted",
        "rejected": "Rejected",
        "waitlisted": "Waitlisted",
        "interview": "Interview",
    }
    return mapping.get(d, str(decision).strip())


def parse_notification(notification: Any) -> dict:
    """
    Extract notification_date and notification_method from a notification string when possible.
    """
    notification = blank_to_none(notification)
    if notification is None:
        return {"notification_date": None, "notification_method": None}

    text = str(notification).strip()

    # Matches things like: "on 30/01/2026 via E-mail" or "on 12/01/2026 via Website"
    m = re.search(r"on\s+(\d{1,2}/\d{1,2}/\d{4})", text, re.IGNORECASE)
    date = m.group(1) if m else None

    method = None
    if "email" in text.lower() or "e-mail" in text.lower():
        method = "E-mail"
    elif "website" in text.lower():
        method = "Website"

    return {"notification_date": date, "notification_method": method}


## ============================================================
## Record cleaning: transform one scraped record into a cleaned record
## ============================================================

def clean_record(record: dict) -> dict:
    """
    Convert one scraped record into a cleaned record with normalized types and parsed notification fields.
    """
    notif = parse_notification(record.get("notification"))

    cleaned = {
        "url": record.get("url"),
        "institution": blank_to_none(record.get("institution")),
        "program": blank_to_none(record.get("program")),
        "degree": blank_to_none(record.get("degree")),
        "country_of_origin": blank_to_none(record.get("country_of_origin")),
        "decision": normalize_decision(record.get("decision")),
        "notification_date": notif["notification_date"],
        "notification_method": notif["notification_method"],
        "undergrad_gpa": to_float(record.get("undergrad_gpa")),
        "gre_general": to_int(record.get("gre_general")),
        "gre_verbal": to_int(record.get("gre_verbal")),
        "gre_aw": to_float(record.get("gre_aw")),
        "notes": blank_to_none(record.get("notes")),
    }
    return cleaned


## ============================================================
## Main pipeline: load JSON, clean all records, and save output JSON
## ============================================================

def main() -> None:
    """
    Load applicant_data.json, clean all records, and write cleaned_applicant_data.json.
    """
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        records = json.load(f)

    cleaned_records = [clean_record(r) for r in records]

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(cleaned_records, f, indent=2, ensure_ascii=False)

    print(f"Loaded {len(records)} records from {INPUT_JSON}")
    print(f"Wrote {len(cleaned_records)} cleaned records to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
