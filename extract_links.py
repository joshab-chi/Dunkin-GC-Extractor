#!/usr/bin/env python3
"""
Step 1: Read downloaded emails and pull out the gift-card reveal links.

Reads every .eml and .mbox file in ./emails/ (no IMAP, no credentials —
just files you exported from Gmail) and writes ./output/links.csv.

Usage:
    python extract_links.py                       # extract all links
    python extract_links.py --domain example.com  # only links on that host
"""

import argparse
import csv
import email
import mailbox
import re
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime
from pathlib import Path

from bs4 import BeautifulSoup

EMAILS_DIR = Path(__file__).parent / "emails"
OUTPUT_CSV = Path(__file__).parent / "output" / "links.csv"

URL_RE = re.compile(r"https?://[^\s\"'<>)]+")


def decode(value):
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return value


def iter_messages():
    """Yield (source_name, email.message.Message) from every .eml and .mbox."""
    for path in sorted(EMAILS_DIR.glob("*.eml")):
        with open(path, "rb") as fh:
            yield path.name, email.message_from_binary_file(fh)
    for path in sorted(EMAILS_DIR.glob("*.mbox")):
        for i, msg in enumerate(mailbox.mbox(str(path))):
            yield f"{path.name}#{i}", msg


def body_html_and_text(msg):
    html, text = "", ""
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            if part.get_content_disposition() == "attachment":
                continue
            try:
                payload = part.get_payload(decode=True)
            except Exception:
                continue
            if not payload:
                continue
            charset = part.get_content_charset() or "utf-8"
            decoded = payload.decode(charset, errors="replace")
            if ctype == "text/html":
                html += decoded
            elif ctype == "text/plain":
                text += decoded
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            decoded = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
            if msg.get_content_type() == "text/html":
                html = decoded
            else:
                text = decoded
    return html, text


def links_from_message(msg, anchor=None):
    """Return list of (anchor_text, url). If `anchor` is given, keep only
    links whose visible text contains it (case-insensitive)."""
    html, text = body_html_and_text(msg)
    found = []
    if html:
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            txt = a.get_text(strip=True)
            if anchor and anchor.lower() not in txt.lower():
                continue
            found.append((txt, a["href"]))
    if not anchor:
        # Also catch bare URLs in plain-text bodies.
        found.extend(("", u) for u in URL_RE.findall(text))
    # De-dupe by URL while preserving order.
    seen, unique = set(), []
    for txt, url in found:
        if url not in seen:
            seen.add(url)
            unique.append((txt, url))
    return unique


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", help="keep only links whose host contains this string")
    ap.add_argument("--anchor", help="keep only links whose visible text contains this "
                                      "(e.g. 'Get Your Card')")
    args = ap.parse_args()

    rows = []
    for source, msg in iter_messages():
        subject = decode(msg.get("Subject"))
        try:
            date = parsedate_to_datetime(msg.get("Date")).isoformat()
        except Exception:
            date = ""
        for anchor_text, url in links_from_message(msg, anchor=args.anchor):
            if args.domain and args.domain not in url:
                continue
            rows.append({"source_file": source, "date": date,
                         "subject": subject, "anchor_text": anchor_text, "url": url})

    OUTPUT_CSV.parent.mkdir(exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["source_file", "date", "subject", "anchor_text", "url"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Parsed emails from {EMAILS_DIR}")
    print(f"Wrote {len(rows)} link(s) to {OUTPUT_CSV}")
    if not args.domain:
        hosts = {}
        for r in rows:
            host = re.sub(r"https?://([^/]+).*", r"\1", r["url"])
            hosts[host] = hosts.get(host, 0) + 1
        print("\nLinks by host (use --domain to filter to the right one):")
        for host, n in sorted(hosts.items(), key=lambda x: -x[1]):
            print(f"  {n:4}  {host}")


if __name__ == "__main__":
    main()
