"""
scrape.py

Scrape GradCafe survey pages to collect result URLs and parse key application fields
from each result page into applicant_data.json.
"""

import json
import re
import socket
import time
import urllib.error
import urllib.request
from typing import Callable

from bs4 import BeautifulSoup


## ============================================================
## Configuration: base URLs, headers, and output file name
## ============================================================

BASE_URL = "https://www.thegradcafe.com"
SURVEY_URL = "https://www.thegradcafe.com/survey/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
OUTPUT_JSON = "applicant_data.json"


## ============================================================
## HTTP Utilities: fetch HTML from a URL using urllib
## ============================================================

def fetch_html(url: str, timeout: int = 30) -> str:
    """
    Download raw HTML from a URL using urllib with a browser-like User-Agent header.
    """
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def safe_fetch_html(
    url: str,
    timeout: int = 30,
    retries: int = 3,
    backoff_sec: float = 1.0,
) -> str | None:
    """
    Fetch HTML with retries so one timeout/429 doesn't crash the entire scrape.
    """
    for attempt in range(1, retries + 1):
        try:
            return fetch_html(url, timeout=timeout)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            print(f"WARNING: fetch failed ({attempt}/{retries}) for {url}: {exc}")
            time.sleep(backoff_sec * attempt)
    return None


## ============================================================
## Survey Page Parsing: collect unique /result/<id> links
## ============================================================

def extract_result_urls_from_survey(html: str) -> list[str]:
    """
    Parse a GradCafe survey listing page and return unique full result URLs found on that page.
    """
    soup = BeautifulSoup(html, "html.parser")

    result_paths: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if re.match(r"^/result/\d+$", href):
            result_paths.add(href)

    return [BASE_URL + p for p in sorted(result_paths)]


## ============================================================
## Result Page Parsing: turn dt/dd pairs into a dictionary
## ============================================================

def _apply_label_mapping(record: dict, label: str, value: str | None) -> None:
    """
    Map a <dt> label string into the correct record field, if recognized.
    """
    mappings: list[tuple[Callable[[str], bool], str]] = [
        (lambda s: "institution" in s, "institution"),
        (lambda s: "program" in s, "program"),
        (lambda s: "degree type" in s, "degree"),
        (lambda s: "country of origin" in s, "country_of_origin"),
        (lambda s: "decision" in s, "decision"),
        (lambda s: "notification" in s, "notification"),
        (lambda s: "undergrad gpa" in s, "undergrad_gpa"),
        (lambda s: "comments" in s, "comments"),
        (lambda s: ("date of information added" in s) or ("date added" in s), "date_added"),
        (lambda s: ("semester" in s) or ("term" in s) or ("program start" in s), "start_term"),
        (lambda s: "notes" in s, "notes"),
    ]

    for predicate, key in mappings:
        if predicate(label):
            record[key] = value
            return


def _apply_gre_mapping(record: dict, text: str) -> None:
    """
    Map GRE list item text into record GRE fields, if recognized.
    """
    gre_mappings: list[tuple[str, str]] = [
        ("gre general", "gre_general"),
        ("gre verbal", "gre_verbal"),
        ("analytical writing", "gre_aw"),
    ]

    for needle, key in gre_mappings:
        if needle in text:
            record[key] = text.split(":")[-1].strip()
            return


def parse_result_page(url: str) -> dict:
    """
    Download one GradCafe result page and extract structured application fields
    from the Application Information <dl> block.
    """
    html = safe_fetch_html(url)
    if html is None:
        return {
            "url": url,
            "institution": None,
            "program": None,
            "degree": None,
            "country_of_origin": None,
            "decision": None,
            "notification": None,
            "undergrad_gpa": None,
            "gre_general": None,
            "gre_verbal": None,
            "gre_aw": None,
            "comments": None,
            "date_added": None,
            "start_term": None,
            "notes": None,
        }

    soup = BeautifulSoup(html, "html.parser")

    record = {
        "url": url,
        "institution": None,
        "program": None,
        "degree": None,
        "country_of_origin": None,
        "decision": None,
        "notification": None,
        "undergrad_gpa": None,
        "gre_general": None,
        "gre_verbal": None,
        "gre_aw": None,
        "comments": None,
        "date_added": None,
        "start_term": None,
        "notes": None,
    }

    dl = soup.find("dl", class_=re.compile(r"\btw-grid\b"))
    if not dl:
        return record

    for dt in dl.find_all("dt"):
        label = dt.get_text(" ", strip=True).lower()
        dd = dt.find_next_sibling("dd")
        value = dd.get_text(" ", strip=True) if dd else None
        _apply_label_mapping(record, label, value)

    for li in dl.find_all("li"):
        text = li.get_text(" ", strip=True).lower()
        _apply_gre_mapping(record, text)

    return record


## ============================================================
## Save Utilities: dump records into JSON
## ============================================================

def save_json(records: list[dict], path: str) -> None:
    """
    Save a list of applicant record dictionaries to a JSON file.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


## ============================================================
## Main: loop survey pages, collect result URLs, parse results, save JSON
## ============================================================

def load_existing_records(path: str) -> list[dict]:
    """
    Load existing JSON records from disk, or return an empty list if not found/invalid.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("WARNING: Existing JSON is corrupted/partial. Starting fresh.")
        return []


def scrape_data(max_pages: int = 5, delay_sec: float = 0.5) -> list[dict]:
    """
    Scrape multiple survey pages, parse each result URL, and return a list of applicant records.
    Resumes from OUTPUT_JSON if it already exists.
    """
    all_urls: set[str] = set()

    for page_num in range(max_pages):
        page_url = f"{SURVEY_URL}?page={page_num}"
        print(f"Scraping survey page: {page_url}")

        html = safe_fetch_html(page_url)
        if html is None:
            continue

        urls = extract_result_urls_from_survey(html)
        all_urls.update(urls)

        time.sleep(delay_sec)

    result_urls = sorted(all_urls)
    print(f"Total unique result URLs found: {len(result_urls)}")

    records = load_existing_records(OUTPUT_JSON)
    seen = {r.get("url") for r in records if isinstance(r, dict) and r.get("url")}

    for url in result_urls:
        if url in seen:
            continue

        print(f"Parsing: {url}")
        rec = parse_result_page(url)
        records.append(rec)
        seen.add(url)

        time.sleep(delay_sec)

        if len(records) % 500 == 0:
            save_json(records, OUTPUT_JSON)
            print(f"Checkpoint saved at {len(records)} records")

    save_json(records, OUTPUT_JSON)
    print(f"Built {len(records)} applicant records")
    return records


if __name__ == "__main__":
    scraped_records = scrape_data(max_pages=2000, delay_sec=0.5)
    save_json(scraped_records, OUTPUT_JSON)
    print(f"Saved {OUTPUT_JSON}")
