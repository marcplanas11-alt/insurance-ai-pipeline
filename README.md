# Insuretechdaily v2

Automated daily job search system for insurance operations roles across Europe.

## What it does

**Daily (Mon–Fri at 8am UTC):**
1. **Job Hunter** — Scans 30+ insurtech/insurance companies via working APIs (Ashby, Greenhouse, Lever, Remotive, RSS), filters for EU-eligible remote roles, scores with Claude AI, generates tailored PDF CVs + cover letters in EN/ES, and emails matches.
2. **Company Scanner** — Monitors 7 RSS feeds for EU insurtech news (funding, launches, expansions).

**Weekly (Monday 9am UTC):**
3. **Weekly Digest** — Summary email with stats, top matches, and action items.

## Architecture

| File | Purpose |
|------|---------|
| `marc_profile.py` | Professional profile (real CV data, skills, scoring keywords) |
| `job_hunter.py` | Job scanning, AI scoring, PDF generation, email alerts |
| `company_scanner.py` | Insurtech news monitoring via RSS |
| `weekly_digest.py` | Weekly summary from tracker CSV |
| `.github/workflows/job-monitor.yml` | GitHub Actions orchestration |

## Job Sources (all working, tested)

| Source | Type | Companies |
|--------|------|-----------|
| Ashby API | JSON | Descartes, Cytora, Artificial Labs, wefox, Alan, Marshmallow, Zego + more |
| Greenhouse API | JSON | Shift Technology, Tractable, Guidewire, Duck Creek, Hokodo + more |
| Lever API | JSON | Wakam, Prima, Superscript, Laka, Flock |
| Remotive API | JSON | All remote insurance/finance jobs |
| RSS feeds | XML | Remotive, We Work Remotely |
| Career pages | HTML | Accelerant, Ledgebrook, Swiss Re, Munich Re, Gen Re, SCOR + more |

## Setup

### GitHub Secrets required:
```
GMAIL_USER          — Gmail address for sending alerts
GMAIL_APP_PASSWORD  — Gmail App Password (not regular password)
ANTHROPIC_API_KEY   — Claude API key for AI scoring + PDF generation
```

### Manual trigger:
Go to Actions tab → "EU Insurance Remote Job Monitor v2" → Run workflow → Choose job type.

## Scoring

Jobs are scored 0-100 by Claude AI:
- **90-100**: Perfect match (insurance ops, remote EU, senior)
- **80-89**: Strong match (ops at insurer/insurtech/MGA)
- **75-79**: Good match (adjacent role at insurance company)
- **<75**: Below threshold — not emailed

Hard rejects: on-site outside Barcelona, junior roles, non-insurance, salary <€50K.

## Caching

Uses `actions/cache/save` and `actions/cache/restore` with content-hash keys. This ensures:
- Cache persists across runs (no `run_id` in key)
- New cache only saved when content actually changes
- Graceful fallback to most recent cache via `restore-keys` prefix
