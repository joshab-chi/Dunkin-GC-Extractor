---
description: Run the gift-card extractor pipeline (emails -> codes/PINs + screenshots -> CSV/xlsx)
---

Run the gift-card extraction pipeline in this project. An optional argument
overrides the reveal-link text (default is Dunkin's "Get Your Card"):
`$ARGUMENTS`

Do the following:

1. **Setup check.** If `.venv/` does not exist, run `./setup.sh` and wait for it
   to finish. Then use the venv's Python (`.venv/bin/python`) for the steps below.

2. **Emails check.** Confirm there is at least one `.mbox` or `.eml` file in
   `emails/`. If it's empty, tell the user to export their gift-card emails into
   `emails/` (see README Step 0 — Gmail label + Google Takeout) and STOP.

3. **Test first.** Run a single-card test before the full batch:
   `.venv/bin/python run.py --limit 1` (add `--anchor "<text>"` if an argument
   was given). Read `output/gift_cards.csv` and show the user the one result.
   If the code/PIN are blank, inspect `output/pages/001.txt` and adjust the
   patterns at the top of `scrape.py`, then retry.

4. **Full run.** Once the test looks right, run `.venv/bin/python run.py`
   (passing `--anchor` if provided).

5. **Report.** Summarize: number of cards, any blank codes/PINs or errors, and
   point to `output/gift_cards.csv`, `output/gift_cards.xlsx`, and `screenshots/`.

Safety rules:
- These pages may be **one-time-view** — if unsure, ask the user to manually open
  one link and reload it before batch-scraping (see README).
- Never paste real, full card numbers/PINs into code, comments, or commits.
- Never commit anything under `output/`, `screenshots/`, `emails/`, or
  `browser-profile/` (all git-ignored — keep it that way).
