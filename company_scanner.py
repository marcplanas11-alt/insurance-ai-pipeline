"""
EU Insurtech Company Scanner v2 — Marc Planas
Monitors insurtech news RSS feeds for new companies, funding rounds,
and EU expansion signals. Only uses RSS (no HTML scraping of JS sites).
"""

import os
import json
import smtplib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GMAIL_USER         = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
SEEN_FILE          = "seen_companies.json"
HEADERS            = {"User-Agent": "Mozilla/5.0 (compatible; InsurtechScanner/2.0)"}
TODAY              = datetime.now().strftime("%Y-%m-%d")

INSURTECH_KEYWORDS = [
    "insurtech", "insuretech", "insurance tech", "insurance technology",
    "parametric insurance", "embedded insurance", "digital insurance",
    "insurance platform", "insurance startup", "mga ", "managing general agent",
    "coverholder", "delegated underwriting", "insurance api",
]

EU_KEYWORDS = [
    "eu", "europe", "european", "dublin", "amsterdam", "paris", "berlin",
    "madrid", "barcelona", "munich", "zurich", "vienna", "milan", "brussels",
    "lisbon", "stockholm", "copenhagen", "warsaw", "london",
    "solvency ii", "eiopa", "pan-european", "dach", "benelux", "nordics",
]

# RSS feeds — tested and working (no JS-rendered pages)
RSS_FEEDS = [
    {"name": "InsTech London",        "url": "https://www.instech.london/feed"},
    {"name": "EU-Startups Insurtech", "url": "https://www.eu-startups.com/category/insurtech/feed/"},
    {"name": "EU-Startups Funding",   "url": "https://www.eu-startups.com/category/funding-news/feed/"},
    {"name": "Sifted",                "url": "https://sifted.eu/feed"},
    {"name": "AltFi",                 "url": "https://www.altfi.com/feed"},
    {"name": "Fintech Global",        "url": "https://fintech.global/category/insurtech/feed/"},
    {"name": "Insurance Edge",        "url": "https://insurance-edge.net/feed/"},
]


def fetch(url, timeout=15):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        return r if r.status_code == 200 else None
    except Exception as e:
        print(f"  fetch error: {str(e)[:50]}")
        return None


def is_relevant(text):
    t = text.lower()
    return any(kw in t for kw in INSURTECH_KEYWORDS)


def has_eu_signal(text):
    t = text.lower()
    return any(kw in t for kw in EU_KEYWORDS)


def load_seen():
    try:
        return set(json.load(open(SEEN_FILE)))
    except Exception:
        return set()


def save_seen(seen):
    json.dump(list(seen), open(SEEN_FILE, "w"))


def scan_rss_feeds():
    """Parse RSS feeds for insurtech-related articles with EU mentions."""
    results = []
    for feed in RSS_FEEDS:
        r = fetch(feed["url"])
        if not r:
            print(f"  {feed['name']}: no response")
            continue
        try:
            root = ET.fromstring(r.content)
            items = root.findall(".//item")
            count = 0
            for item in items:
                title = (item.findtext("title") or "").strip()
                desc  = (item.findtext("description") or "").strip()
                link  = (item.findtext("link") or "").strip()
                pub   = (item.findtext("pubDate") or "").strip()
                text  = f"{title} {desc}"

                if is_relevant(text) and has_eu_signal(text):
                    results.append({
                        "title": title[:150],
                        "source": feed["name"],
                        "url": link,
                        "snippet": desc[:250],
                        "date": pub[:16] if pub else TODAY,
                    })
                    count += 1
            print(f"  {feed['name']}: {count} relevant article(s) from {len(items)} total")
        except ET.ParseError as e:
            print(f"  {feed['name']}: XML parse error — {e}")
        except Exception as e:
            print(f"  {feed['name']}: error — {e}")
    return results


def find_new(all_articles, seen):
    new = []
    for article in all_articles:
        key = f"{article['source']}|{article['title']}"
        if key not in seen and len(article["title"]) > 15:
            new.append((key, article))
    # Deduplicate by title similarity
    seen_titles = set()
    deduped = []
    for key, article in new:
        short_title = article["title"][:60].lower()
        if short_title not in seen_titles:
            seen_titles.add(short_title)
            deduped.append((key, article))
    return deduped


def send_email(new_articles):
    if not GMAIL_USER:
        print("  No email credentials — skipping send")
        return

    subject = f"🚀 {len(new_articles)} Insurtech News Alert — {TODAY}"

    rows = ""
    for _, article in new_articles:
        snippet = (article.get("snippet", "")[:150] + "...") if article.get("snippet") else ""
        rows += f"""
        <tr>
          <td style="padding:10px;border-bottom:1px solid #eee;font-weight:bold;color:#1a2744;">
            {article['title'][:100]}
          </td>
          <td style="padding:10px;border-bottom:1px solid #eee;color:#666;font-size:12px;">
            {article['source']}
          </td>
          <td style="padding:10px;border-bottom:1px solid #eee;font-size:11px;color:#555;">
            {snippet}
          </td>
          <td style="padding:10px;border-bottom:1px solid #eee;">
            <a href="{article['url']}" style="color:#2563eb;">Read →</a>
          </td>
        </tr>"""

    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:750px;margin:auto;">
<div style="background:linear-gradient(135deg,#1a2744,#2563eb);padding:20px;border-radius:8px;margin-bottom:16px;">
  <h2 style="color:#fff;margin:0;">🚀 Insurtech News Alert</h2>
  <p style="color:#ddd;margin:6px 0 0;">{TODAY} · {len(new_articles)} new article(s) with EU insurtech mentions</p>
</div>
<table style="width:100%;border-collapse:collapse;">
  <thead><tr style="background:#f4f4f4;">
    <th style="padding:8px;text-align:left;">Article</th>
    <th style="padding:8px;text-align:left;">Source</th>
    <th style="padding:8px;text-align:left;">Summary</th>
    <th style="padding:8px;text-align:left;">Link</th>
  </tr></thead>
  <tbody>{rows}</tbody>
</table>
<p style="font-size:11px;color:#999;margin-top:20px;border-top:1px solid #eee;padding-top:12px;">
  EU Insurtech Company Scanner v2 · {len(RSS_FEEDS)} RSS feeds monitored · {TODAY}
</p></body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Insurtech Scanner <{GMAIL_USER}>"
    msg["To"] = GMAIL_USER
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        print(f"✅ Email sent: {len(new_articles)} article(s)")
    except Exception as e:
        print(f"❌ Email error: {e}")


def main():
    print(f"\n{'='*50}")
    print(f"  EU Insurtech Company Scanner v2 — {TODAY}")
    print(f"{'='*50}\n")

    seen = load_seen()
    all_articles = scan_rss_feeds()
    new_ones = find_new(all_articles, seen)

    print(f"\n📊 Total relevant articles: {len(all_articles)}")
    print(f"🆕 New (not seen before): {len(new_ones)}")

    if new_ones:
        send_email(new_ones)
        seen.update(key for key, _ in new_ones)
        save_seen(seen)
    else:
        print("✅ No new insurtech articles today.")


if __name__ == "__main__":
    main()
