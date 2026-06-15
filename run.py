#!/usr/bin/env python3
"""
One-shot pipeline: extract links -> scrape codes/PINs + screenshots -> build xlsx.

Run after ./setup.sh, with the virtualenv active:

    python run.py                       # full batch (Dunkin default anchor)
    python run.py --limit 1             # quick test on one card
    python run.py --anchor "View Card"  # different retailer's link text
"""

import argparse
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
EMAILS = BASE / "emails"


def step(name, script_args):
    print(f"\n=== {name} ===", flush=True)
    result = subprocess.run([sys.executable, *script_args], cwd=BASE)
    if result.returncode != 0:
        sys.exit(f"\n{name} failed (exit {result.returncode}). Stopping.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--anchor", default="Get Your Card",
                    help='visible text of the reveal link (default: "Get Your Card")')
    ap.add_argument("--limit", type=int, default=0,
                    help="only process the first N cards (0 = all); use 1 to test")
    ap.add_argument("--headful", action="store_true",
                    help="show the browser window (for logging in / debugging)")
    ap.add_argument("--no-xlsx", action="store_true",
                    help="skip building the .xlsx with embedded screenshots")
    args = ap.parse_args()

    # Friendly pre-flight: make sure there's something to process.
    emails = list(EMAILS.glob("*.mbox")) + list(EMAILS.glob("*.eml"))
    if not emails:
        sys.exit(f"No .mbox/.eml files in {EMAILS}/.\n"
                 "Export your gift-card emails there first (see README Step 0).")
    print(f"Found {len(emails)} email file(s) in {EMAILS}/")

    step("Extract links", ["extract_links.py", "--anchor", args.anchor])

    scrape = ["scrape.py"]
    if args.limit:
        scrape += ["--limit", str(args.limit)]
    if args.headful:
        scrape += ["--headful"]
    step("Scrape codes + screenshots", scrape)

    if not args.no_xlsx:
        step("Build spreadsheet with screenshots", ["build_xlsx.py"])

    print("\nDone. Outputs:")
    print("  output/gift_cards.csv")
    if not args.no_xlsx:
        print("  output/gift_cards.xlsx  (with embedded screenshots)")
    print("  screenshots/*.png")


if __name__ == "__main__":
    main()
