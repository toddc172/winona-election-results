#!/usr/bin/env python3
"""Fetch Minnesota SOS 2026 general-election result files and publish one JSON bundle.

Designed for GitHub Actions. Uses only the Python standard library.
If a source fetch fails, the script retains the previous last-known-good copy of that feed.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URL = "https://electionresultsfiles.sos.mn.gov/20261103/"
OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "results.json"
USER_AGENT = "WinonaDailyNews-ElectionResultsRelay/1.0 (+https://winonadailynews.com/)"
TIMEOUT = 30
RETRIES = 3

FEEDS = [
    "ussenate.txt",
    "ushouse.txt",
    "Governor.txt",
    "secofstate.txt",
    "auditor.txt",
    "attorneygen.txt",
    "stsenate.txt",
    "LegislativeByDistrict.txt",
    "cntyRaces.txt",
    "local.txt",
    "sdrace.txt",
    "judicial.txt",
    "judicialdst.txt",
    "ConstAmend.txt",
    "SDRaceQuestions.txt",
]


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_previous() -> dict:
    if not OUTPUT.exists():
        return {}
    try:
        return json.loads(OUTPUT.read_text(encoding="utf-8"))
    except Exception:
        return {}


def decode_body(raw: bytes) -> str:
    # State files are documented as ASCII, but utf-8-sig and cp1252 make the relay tolerant
    # of a BOM or punctuation introduced upstream.
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1")


def validate_feed(text: str) -> None:
    if not text.strip():
        raise ValueError("State file was empty")
    # The SOS result format is semicolon-delimited. Avoid replacing a good cached feed
    # with an HTML error page or another unexpected response.
    rows = [line for line in text.splitlines() if line.strip()]
    if not any(line.count(";") >= 10 for line in rows):
        raise ValueError("Response did not look like a semicolon-delimited SOS results file")


def fetch_one(filename: str) -> tuple[str, int]:
    url = BASE_URL + filename
    last_error: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/plain,*/*;q=0.8",
                    "Cache-Control": "no-cache",
                },
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
                status = getattr(response, "status", 200)
                raw = response.read()
            text = decode_body(raw)
            validate_feed(text)
            return text, int(status)
        except Exception as exc:  # noqa: BLE001 - preserve useful error text in output
            last_error = exc
            if attempt < RETRIES:
                time.sleep(attempt * 2)
    assert last_error is not None
    raise last_error


def main() -> int:
    previous = load_previous()
    previous_feeds = previous.get("feeds", {}) if isinstance(previous, dict) else {}
    now = iso_now()
    feeds: dict[str, dict] = {}
    successes = 0
    stale = 0
    unavailable = 0

    for filename in FEEDS:
        url = BASE_URL + filename
        old = previous_feeds.get(filename, {}) if isinstance(previous_feeds, dict) else {}
        try:
            text, status = fetch_one(filename)
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            feeds[filename] = {
                "file": filename,
                "sourceUrl": url,
                "available": True,
                "stale": False,
                "httpStatus": status,
                "fetchedAt": now,
                "lastAttemptAt": now,
                "sha256": digest,
                "error": None,
                "text": text,
            }
            successes += 1
            print(f"OK   {filename}: {len(text):,} chars")
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"
            old_text = old.get("text") if isinstance(old, dict) else None
            if old_text:
                feeds[filename] = {
                    "file": filename,
                    "sourceUrl": url,
                    "available": True,
                    "stale": True,
                    "httpStatus": old.get("httpStatus"),
                    "fetchedAt": old.get("fetchedAt"),
                    "lastAttemptAt": now,
                    "sha256": old.get("sha256"),
                    "error": error,
                    "text": old_text,
                }
                stale += 1
                print(f"STALE {filename}: {error}", file=sys.stderr)
            else:
                feeds[filename] = {
                    "file": filename,
                    "sourceUrl": url,
                    "available": False,
                    "stale": True,
                    "httpStatus": None,
                    "fetchedAt": None,
                    "lastAttemptAt": now,
                    "sha256": None,
                    "error": error,
                    "text": "",
                }
                unavailable += 1
                print(f"FAIL  {filename}: {error}", file=sys.stderr)

    bundle = {
        "meta": {
            "schemaVersion": 1,
            "election": "2026 Minnesota State General Election",
            "electionDate": "2026-11-03",
            "source": "Minnesota Secretary of State",
            "sourceBaseUrl": BASE_URL,
            "generatedAt": now,
            "feedCount": len(FEEDS),
            "successfulFeeds": successes,
            "staleFeeds": stale,
            "unavailableFeeds": unavailable,
        },
        "feeds": feeds,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temp = OUTPUT.with_suffix(".json.tmp")
    temp.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, OUTPUT)
    print(
        f"Wrote {OUTPUT}: {successes} fresh, {stale} cached/stale, "
        f"{unavailable} unavailable."
    )
    # Do not fail the workflow solely because one feed is temporarily unavailable;
    # the JSON status lets BLOX report the condition and cached data remains usable.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
