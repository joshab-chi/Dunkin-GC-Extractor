# Gift Card Extractor

Pulls gift-card codes + PINs out of order-confirmation emails and into a CSV,
with a screenshot of every reveal page. **Runs entirely on your Mac** — no IMAP,
no app password, no cloud. You export the emails to files; the scripts read them
off disk.

## Layout

```
emails/        <- you drop exported .eml / .mbox files here
screenshots/   <- one PNG per gift card (created by scrape.py)
output/
  links.csv      <- extracted reveal links (extract_links.py)
  gift_cards.csv <- final result: code, pin, screenshot, etc. (scrape.py)
  pages/         <- saved page text, for tuning the scraper
browser-profile/ <- persistent browser session (remembers retailer login)
```

> **Note:** out of the box this is tuned for **Dunkin'** e-gift emails. For a
> different retailer you'll adjust two things: the `--anchor` text in Step 1
> (the wording on the "view your card" link) and the `CODE_PATTERNS` /
> `PIN_PATTERNS` regexes at the top of `scrape.py`. See Step 2.

## One-time setup

```bash
cd gift-card-extractor
./setup.sh            # creates .venv, installs deps, downloads the browser
```

<details>
<summary>Or do it manually</summary>

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```
</details>

## Run it all at once

After setup and dropping your emails in `emails/` (Step 0 below):

```bash
source .venv/bin/activate
python run.py --limit 1     # test one card first
python run.py               # then the full batch
```

`run.py` chains the three steps (extract links → scrape → build spreadsheet).
Override the reveal-link text for other retailers with `--anchor "<text>"`.

### Via Claude Code

This repo ships a `/extract` slash command and a `CLAUDE.md`, so inside Claude
Code you can just run **`/extract`** (or ask "run the extractor") and Claude will
do setup, a one-card test, the full batch, and report results — following the
safety rules in `CLAUDE.md`.

## Step 0 — Export the emails from Gmail (no IMAP)

You give the tool the emails as files — no password or IMAP needed. For more
than a handful of cards, use the Google Takeout route below.

### Recommended: gather the emails under a label, then export with Takeout

**Part A — put all the gift-card emails under one Gmail label**

1. Open Gmail in a web browser and sign in.
2. In the search bar, search for the gift-card emails — typically by sender,
   e.g. `from:giftcards@theretailer.com`. (For Dunkin':
   `from:dunkinrewards@email.dunkinrewards.com`.) Press Enter.
3. Skim the results to confirm they're the right emails. If marketing is mixed
   in, tighten the search, e.g. add `subject:(gift card)`.
4. Select them all: click the checkbox at the top-left of the list, then click
   **"Select all conversations that match this search"** if it appears (so you
   get every match, not just the first page).
5. Click the **label icon** (a tag) in the toolbar → **Create new** → name it
   `giftcards` → **Create**. This tags every selected email with that label.

**Part B — export just that label as a single .mbox file**

1. Go to **https://takeout.google.com** (signed in to the same account).
2. Click **Deselect all** at the top (so you don't export your entire account).
3. Scroll down to **Mail** and check its box.
4. Under Mail, click **All Mail data included** → in the popup click
   **Deselect all** → check only **`giftcards`** → **OK**. *(This is the key
   step — otherwise Takeout exports your whole mailbox.)*
5. Scroll to the bottom → **Next step**.
6. Leave the defaults (Send download link via email, Export once, .zip) →
   **Create export**. A small label usually finishes in a few minutes.
7. When the email arrives, download and unzip it. Inside is a `.mbox` file
   (e.g. `giftcards.mbox`).
8. Move that `.mbox` file into this project's **`emails/`** folder.

### Alternative: a few at a time

Open a gift-card email in Gmail → the "⋮" menu (top right of the message) →
**Download message** → saves a `.eml`. Drop it into `emails/`. Fine for a
handful; tedious for many.

> The scripts read every `.eml` **and** `.mbox` file in `emails/`, so you can
> mix both. The `emails/` folder is git-ignored — your emails never get shared
> or committed.

## Step 1 — Extract the links

```bash
python extract_links.py
```

It prints a breakdown of links by host. Find the retailer's host, then re-run
filtered so `links.csv` only has the real reveal links:

```bash
python extract_links.py --domain theretailer.com
```

## Step 2 — Scrape codes + screenshots

**Test on ONE card first**, with the browser visible (and log in if the page
asks you to — it'll be remembered next time):

```bash
python scrape.py --headful --limit 1
```

Open `output/gift_cards.csv` and `screenshots/card_001.png` to check it worked.
If code/PIN are blank, look at `output/pages/001.txt` and adjust the
`CODE_PATTERNS` / `PIN_PATTERNS` / selectors at the top of `scrape.py`.

Then run the full batch:

```bash
python scrape.py
```

## Step 3 (optional) — Spreadsheet with embedded screenshots

```bash
python build_xlsx.py
```

Writes `output/gift_cards.xlsx` with each card's screenshot embedded in its row.
Open in Excel/Numbers (images show inline) or upload to Google Drive.

## Leading zeros

Codes/PINs that start with `0` are written to `gift_cards.csv` with a leading
apostrophe (e.g. `'05495962`) so Excel/Google Sheets keep them as text instead
of dropping the zero. The `.xlsx` stores them as text cells directly (no
apostrophe needed).


## Security note

`gift_cards.csv`, the screenshots, and `output/pages/` contain live, spendable
codes. Keep this folder private; consider deleting `browser-profile/` and the
page dumps when you're done.

## Disclaimer — use at your own risk

This tool is provided **as is**, without warranty of any kind (see `LICENSE`).
By using it you accept full responsibility for what it does on your machine and
accounts. In particular:

- **Only use it on gift cards you own** and emails in your own mailbox.
- It opens links from your emails in a real browser. 
- Output files hold spendable codes. The author is not liable for any loss,
  lost cards, account actions, or other damages arising from its use.
