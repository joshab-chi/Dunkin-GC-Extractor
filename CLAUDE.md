# Dunkin GC Extractor — notes for Claude Code

Local tool that pulls gift-card codes + PINs (and a screenshot per card) out of
order-confirmation emails into a CSV/XLSX. Runs entirely on the user's machine.

## Running it

Quickest path: the `/extract` slash command, or just run the one-shot pipeline:

```bash
./setup.sh                      # once: venv + deps + browser (skip if .venv exists)
source .venv/bin/activate
python run.py --limit 1         # test one card first
python run.py                   # full batch
```

`run.py` chains `extract_links.py` -> `scrape.py` -> `build_xlsx.py`. The default
reveal-link anchor is Dunkin's `"Get Your Card"`; override with `--anchor`.

Inputs go in `emails/` (`.mbox`/`.eml`, exported from Gmail — see README Step 0).
Outputs land in `output/` (`gift_cards.csv`, `gift_cards.xlsx`) and `screenshots/`.

## Retailer-specific bits (the only things to tune for a new sender)

- The `--anchor` text (visible label of the "view your card" link).
- `CODE_PATTERNS` / `PIN_PATTERNS` (and optional CSS selectors) at the top of
  `scrape.py`. Use `--limit 1` and inspect `output/pages/001.txt` to dial these in.

## Safety rules (important)

- **Output is spendable cash.** `output/`, `screenshots/`, `emails/`, and
  `browser-profile/` are git-ignored — never commit them.
- **Never put real card numbers/PINs in code, comments, or commit messages.**
  Use obvious placeholders (e.g. `1234 5678 9012 3456`). 
- Some reveal pages are **one-time-view**; an automated open can burn them. When
  unsure, have the user open one link manually and reload before batch-scraping.
