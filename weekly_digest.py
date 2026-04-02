"""
Weekly Digest v2 — Marc Planas Job Hunt
Reads job_tracker.csv and sends a summary email every Monday.
"""

import os
import csv
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from collections import Counter

GMAIL_USER         = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
TRACKER_FILE       = "job_tracker.csv"
TODAY              = datetime.now().strftime("%Y-%m-%d")
WEEK_AGO           = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")


def load_tracker():
    rows = []
    if not os.path.exists(TRACKER_FILE):
        return rows
    try:
        with open(TRACKER_FILE, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rows.append(row)
    except Exception as e:
        print(f"Tracker read error: {e}")
    return rows


def send_digest(all_rows):
    this_week = [r for r in all_rows if r.get("Date", "") >= WEEK_AGO]
    total_all = len(all_rows)
    total_week = len(this_week)
    companies = Counter(r.get("Company", "") for r in this_week)
    sources = Counter(r.get("Source", "") for r in this_week)
    scores = [int(r["Score"]) for r in this_week if r.get("Score", "").isdigit()]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    top_score = max(scores) if scores else 0
    pending = [r for r in all_rows if r.get("Status", "") == "New"]

    # Top matches table
    top_matches = sorted(this_week, key=lambda x: int(x.get("Score", "0") or "0"), reverse=True)[:10]
    rows_html = ""
    for r in top_matches:
        s = int(r.get("Score", "0") or "0")
        color = "#16a34a" if s >= 85 else "#2563eb" if s >= 75 else "#d97706"
        rows_html += f"""<tr>
  <td style="padding:6px 8px;border-bottom:1px solid #eee;font-size:12px;">{r.get('Date','')}</td>
  <td style="padding:6px 8px;border-bottom:1px solid #eee;"><a href="{r.get('Link','')}" style="color:#1a2744;font-size:12px;">{r.get('Title','')[:50]}</a></td>
  <td style="padding:6px 8px;border-bottom:1px solid #eee;font-size:12px;">{r.get('Company','')}</td>
  <td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:center;"><b style="color:{color};">{s}%</b></td>
  <td style="padding:6px 8px;border-bottom:1px solid #eee;font-size:11px;">{r.get('Salary','')}</td>
  <td style="padding:6px 8px;border-bottom:1px solid #eee;font-size:11px;">{r.get('Status','')}</td>
</tr>"""

    top_cos = "".join(f"<li><b>{co}</b> — {n} role(s)</li>" for co, n in companies.most_common(5))
    top_srcs = "".join(f"<li>{s} — {n}</li>" for s, n in sources.most_common(5))

    html = f"""<html><body style="font-family:Arial,sans-serif;max-width:700px;margin:auto;">
<div style="background:linear-gradient(135deg,#1a2744,#2563eb);padding:20px;border-radius:8px 8px 0 0;">
  <h2 style="color:#fff;margin:0;">📊 Weekly Job Hunt Digest</h2>
  <p style="color:#ddd;margin:6px 0 0;">Week ending {TODAY}</p>
</div>
<div style="padding:20px;background:#f8fafc;">
  <table style="width:100%;border-collapse:collapse;margin-bottom:20px;">
    <tr>
      <td style="background:#1a2744;color:white;padding:14px;text-align:center;border-radius:6px;width:24%;">
        <div style="font-size:28px;font-weight:bold;">{total_week}</div>
        <div style="font-size:11px;">This Week</div></td>
      <td style="width:2%;"></td>
      <td style="background:#16a34a;color:white;padding:14px;text-align:center;border-radius:6px;width:24%;">
        <div style="font-size:28px;font-weight:bold;">{avg_score}%</div>
        <div style="font-size:11px;">Avg Score</div></td>
      <td style="width:2%;"></td>
      <td style="background:#2563eb;color:white;padding:14px;text-align:center;border-radius:6px;width:24%;">
        <div style="font-size:28px;font-weight:bold;">{top_score}%</div>
        <div style="font-size:11px;">Top Score</div></td>
      <td style="width:2%;"></td>
      <td style="background:#6b7280;color:white;padding:14px;text-align:center;border-radius:6px;width:24%;">
        <div style="font-size:28px;font-weight:bold;">{total_all}</div>
        <div style="font-size:11px;">All Time</div></td>
    </tr>
  </table>

  <h3 style="color:#1a2744;">Top Companies This Week</h3>
  <ul style="font-size:13px;">{top_cos or "<li>No matches this week</li>"}</ul>

  <h3 style="color:#1a2744;">Top Sources</h3>
  <ul style="font-size:13px;">{top_srcs or "<li>No matches this week</li>"}</ul>

  <h3 style="color:#1a2744;">Top 10 Matches</h3>
  <table style="width:100%;font-size:12px;border-collapse:collapse;border:1px solid #eee;">
    <tr style="background:#1a2744;color:white;">
      <th style="padding:8px;">Date</th><th style="padding:8px;">Role</th>
      <th style="padding:8px;">Company</th><th style="padding:8px;">Score</th>
      <th style="padding:8px;">Salary</th><th style="padding:8px;">Status</th>
    </tr>
    {rows_html or '<tr><td colspan="6" style="padding:12px;text-align:center;color:#888;">No matches</td></tr>'}
  </table>

  <div style="margin-top:20px;padding:14px;background:#fff3cd;border-radius:6px;border-left:4px solid #ffc107;">
    <b>⚡ Action Items:</b> {len(pending)} job(s) not yet applied to.
  </div>
</div>
<div style="background:#1a2744;padding:12px 20px;border-radius:0 0 8px 8px;font-size:11px;color:#aaa;">
  Job Hunter v2 · Weekly Digest · {TODAY}
</div></body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 Weekly Digest {TODAY} — {total_week} matches this week"
    msg["From"] = f"Job Hunter <{GMAIL_USER}>"
    msg["To"] = GMAIL_USER
    msg.attach(MIMEText(f"Weekly Digest {TODAY}: {total_week} matches, avg {avg_score}%", "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())
        print(f"✅ Weekly digest sent: {total_week} matches this week")
    except Exception as e:
        print(f"❌ Email error: {e}")


if __name__ == "__main__":
    if not GMAIL_USER:
        print("⚠ No GMAIL_USER — running in dry mode")
    rows = load_tracker()
    print(f"Tracker rows: {len(rows)}")
    if GMAIL_USER:
        send_digest(rows)
    else:
        print("Skipping email — no credentials")
