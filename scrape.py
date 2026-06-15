#!/usr/bin/env python3
"""
Step 2: Visit each reveal link, screenshot it, and pull out code + PIN.

Reads ./output/links.csv (from extract_links.py), opens each URL in a real
browser via Playwright, saves a full-page screenshot per card, and writes
./output/gift_cards.csv.

Everything runs locally. Uses a persistent browser profile in ./browser-profile/
so any retailer login you do once is remembered on later runs.

First run (set up + log in if needed):
    python scrape.py --headful --limit 1
Then the full batch once selectors are dialed in:
    python scrape.py

Tuning extraction: the CODE_PATTERNS / PIN_PATTERNS regexes and the optional
CSS selectors below are the retailer-specific part. Run with --limit 1 first,
check output/pages/<n>.txt to see the page text, then adjust the patterns.
"""

import argparse
import csv
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).parent
LINKS_CSV = BASE / "output" / "links.csv"
CARDS_CSV = BASE / "output" / "gift_cards.csv"
SHOTS_DIR = BASE / "screenshots"
PAGES_DIR = BASE / "output" / "pages"
PROFILE_DIR = BASE / "browser-profile"

# --- Retailer-specific extraction (adjust after looking at a real page) ------
# Tried in order; first match wins. Add the patterns that fit your retailer.
CODE_PATTERNS = [
    r"Card\s*#\s*:?\s*([0-9][0-9 ]{12,24}[0-9])",     # Dunkin: e.g. "Card #: 1234 5678 9012 3456"
    r"(?:card number|card code|gift card code|code)\s*[:\-]?\s*([A-Z0-9\- ]{8,25})",
]
PIN_PATTERNS = [
    r"Pin\s*:?\s*([0-9]{4,12})",                       # Dunkin: e.g. "Pin: 12345678"
    r"(?:pin|security code|cvv)\s*[:\-]?\s*([0-9]{3,8})",
]
AMOUNT_PATTERNS = [r"\$\s*([0-9]+(?:\.[0-9]{2})?)"]
FROM_PATTERNS = [r"FROM\s*:?\s*(.+)"]
# Optional: if code/PIN live in specific elements, set CSS selectors here.
CODE_SELECTOR = ""  # e.g. ".gift-card-number"
PIN_SELECTOR = ""   # e.g. ".gift-card-pin"
# If the page hides the code behind a button, set its selector to auto-click.
REVEAL_BUTTON_SELECTOR = ""  # e.g. "button:has-text('Reveal')"
# ---------------------------------------------------------------------------


def first_match(patterns, text):
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def text_safe(value):
    """Prepend an apostrophe to values with a leading zero so spreadsheet apps
    (Excel, Google Sheets) keep them as text instead of dropping the zero."""
    value = value.lstrip("'")
    return "'" + value if value.startswith("0") else value


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headful", action="store_true",
                    help="show the browser window (use for first run / logging in)")
    ap.add_argument("--limit", type=int, default=0,
                    help="only process the first N links (0 = all)")
    ap.add_argument("--wait", type=float, default=2.0,
                    help="seconds to wait after load before scraping")
    args = ap.parse_args()

    with open(LINKS_CSV) as fh:
        links = list(csv.DictReader(fh))
    if args.limit:
        links = links[: args.limit]

    SHOTS_DIR.mkdir(exist_ok=True)
    PAGES_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE_DIR), headless=not args.headful)
        page = ctx.new_page()

        for i, row in enumerate(links, start=1):
            url = row["url"]
            print(f"[{i}/{len(links)}] {url}")
            code = pin = ""
            error = ""
            try:
                page.goto(url, wait_until="networkidle", timeout=45000)
                page.wait_for_timeout(int(args.wait * 1000))

                if REVEAL_BUTTON_SELECTOR:
                    btn = page.query_selector(REVEAL_BUTTON_SELECTOR)
                    if btn:
                        btn.click()
                        page.wait_for_timeout(1500)

                shot = SHOTS_DIR / f"card_{i:03}.png"
                page.screenshot(path=str(shot), full_page=True)

                text = page.inner_text("body")
                (PAGES_DIR / f"{i:03}.txt").write_text(text)

                if CODE_SELECTOR:
                    el = page.query_selector(CODE_SELECTOR)
                    code = el.inner_text().strip() if el else ""
                if PIN_SELECTOR:
                    el = page.query_selector(PIN_SELECTOR)
                    pin = el.inner_text().strip() if el else ""
                if not code:
                    code = first_match(CODE_PATTERNS, text)
                if not pin:
                    pin = first_match(PIN_PATTERNS, text)
                amount = first_match(AMOUNT_PATTERNS, text)
                sender = first_match(FROM_PATTERNS, text)
            except Exception as e:
                error = str(e)
                amount = sender = ""
                print(f"    ! {error}")

            results.append({
                "index": i, "code": text_safe(" ".join(code.split())),
                "pin": text_safe(pin),
                "amount": amount, "from": sender,
                "screenshot": f"screenshots/card_{i:03}.png",
                "date": row.get("date", ""), "subject": row.get("subject", ""),
                "url": url, "source_file": row.get("source_file", ""),
                "error": error,
            })

        ctx.close()

    with open(CARDS_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=[
            "index", "code", "pin", "amount", "from", "screenshot", "date",
            "subject", "url", "source_file", "error"])
        writer.writeheader()
        writer.writerows(results)

    ok = sum(1 for r in results if r["code"])
    print(f"\nWrote {len(results)} row(s) to {CARDS_CSV}")
    print(f"Screenshots in {SHOTS_DIR}")
    print(f"Got a code for {ok}/{len(results)} cards.")
    if ok < len(results):
        print("Missing some? Check output/pages/*.txt and tune the patterns at the top of scrape.py.")


if __name__ == "__main__":
    main()
