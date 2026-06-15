#!/usr/bin/env bash
# One-command setup: creates a virtualenv, installs dependencies, and downloads
# the browser Playwright needs. Run once after cloning/unzipping:
#     ./setup.sh
set -euo pipefail
cd "$(dirname "$0")"

echo "==> Creating virtual environment (.venv)"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Installing Python dependencies"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "==> Downloading the Chromium browser for Playwright"
playwright install chromium

echo
echo "Setup complete. Next steps:"
echo "  1. source .venv/bin/activate"
echo "  2. Put your exported .mbox/.eml emails in ./emails/"
echo "  3. python extract_links.py --anchor \"Get Your Card\""
echo "  4. python scrape.py            (add --headful --limit 1 to test first)"
echo "  5. python build_xlsx.py        (optional: spreadsheet with screenshots)"
