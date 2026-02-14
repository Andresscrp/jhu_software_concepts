"""
scrape.py

Scrape GradCafe survey pages to collect result URLs and parse key application fields
from each result page into applicant_data.json.
"""

import re
import json
import time
import urllib.request
import urllib.error
import socket
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


def safe_fetch_html(url: str, timeout: int = 30, retries: int = 3, backoff_sec: float = 1.0) -> str | None:
    """
    Fetch HTML with retries so one timeout/429 doesn't crash the entire scrape.
    """
    for attempt in range(1, retries + 1):
        try:
            return fetch_html(url, timeout=timeout)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, socket.timeout) as e:
            print(f"WARNING: fetch failed ({attempt}/{retries}) for {url}: {e}")
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

    result_paths = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if re.match(r"^/result/\d+$", href):
            result_paths.add(href)

    return [BASE_URL + p for p in sorted(result_paths)]


## ============================================================
## Result Page Parsing: turn dt/dd pairs into a dictionary
## ============================================================

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

        if "institution" in label:
            record["institution"] = value
        elif "program" in label:
            record["program"] = value
        elif "degree type" in label:
            record["degree"] = value
        elif "country of origin" in label:
            record["country_of_origin"] = value
        elif "decision" in label:
            record["decision"] = value
        elif "notification" in label:
            record["notification"] = value
        elif "undergrad gpa" in label:
            record["undergrad_gpa"] = value
        elif "comments" in label:
            record["comments"] = value
        elif "date of information added" in label or "date added" in label:
            record["date_added"] = value
        elif "semester" in label or "term" in label or "program start" in label:
            record["start_term"] = value

        elif "notes" in label:
            record["notes"] = value

    for li in dl.find_all("li"):
        text = li.get_text(" ", strip=True).lower()
        if "gre general" in text:
            record["gre_general"] = text.split(":")[-1].strip()
        elif "gre verbal" in text:
            record["gre_verbal"] = text.split(":")[-1].strip()
        elif "analytical writing" in text:
            record["gre_aw"] = text.split(":")[-1].strip()

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
    # 1) Collect result URLs from survey pages
    all_urls = set()

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

    # 2) Load existing records so we can resume
    records = load_existing_records(OUTPUT_JSON)
    seen = {r.get("url") for r in records if isinstance(r, dict) and r.get("url")}

    # 3) Parse each result page (skip ones we already have)
    for i, url in enumerate(result_urls, start=1):
        if url in seen:
            continue

        print(f"Parsing: {url}")
        rec = parse_result_page(url)
        records.append(rec)
        seen.add(url)

        time.sleep(delay_sec)

        # checkpoint every 500 total saved records
        if len(records) % 500 == 0:
            save_json(records, OUTPUT_JSON)
            print(f"Checkpoint saved at {len(records)} records")

    # final save at the end
    save_json(records, OUTPUT_JSON)
    print(f"Built {len(records)} applicant records")
    return records

if __name__ == "__main__":
    records = scrape_data(max_pages=2000, delay_sec=0.5)
    save_json(records, OUTPUT_JSON)
    print(f"Saved {OUTPUT_JSON}")




