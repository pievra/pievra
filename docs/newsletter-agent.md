# Protocol Intelligence Weekly — Autonomous Newsletter Agent

The Pievra newsletter pipeline is a fully autonomous system that drafts, validates and dispatches a weekly protocol intelligence briefing every Tuesday at 06:00 CET — zero manual intervention.

---

## Architecture

```
Every Tuesday 06:00 CET
        │
        ▼
┌───────────────────┐
│   Orchestrator    │  orchestrator.py
│   (master agent)  │
└──────┬────────────┘
       │
       ├──────────────────────────────────────────┐
       │                                          │
       ▼                                          ▼
┌─────────────┐                         ┌──────────────┐
│  Research   │                         │  Database    │
│  Agent      │                         │  (PostgreSQL)│
│             │                         │              │
│ GitHub ×5   │                         │ Subscribers  │
│ NewsAPI ×3  │                         │ Consent      │
│ RSS ×6      │                         │ Issues log   │
└──────┬──────┘                         └──────────────┘
       │
       ▼
┌─────────────┐
│  Content    │  Claude Sonnet 4
│  Agent      │  Drafts newsletter
│             │  from research data
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Compliance  │  11 GDPR checks
│  Agent      │  Hard stops on
│             │  missing legal elements
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Send      │  Mailgun dispatch
│   Agent     │  Per-subscriber
│             │  unsubscribe tokens
└─────────────┘
```

---

## Data Sources

### GitHub — Protocol Repositories (5 repos)

| Repo | What it tracks |
|---|---|
| `adcontextprotocol/adcp` | AdCP version releases |
| `modelcontextprotocol/modelcontextprotocol` | MCP spec updates |
| `IABTechLab/agentic-rtb-framework` | ARTF releases |
| `IABTechLab/agentic-audiences` | UCP/AAMP releases |
| `google/A2A` | A2A protocol releases |

Requires a GitHub personal access token with `public_repo` scope.

### NewsAPI (3 queries per run)

Queries:
1. `"agentic advertising programmatic AI agents"`
2. `"AdCP IAB Tech Lab ARTF protocol"`
3. `"programmatic advertising adtech 2026"`

Returns up to 5 articles per query from the past 7 days. Covers AdExchanger, Digiday, Marketing Dive, AdWeek, The Drum.

### RSS Feeds (6 sources)

| Source | URL |
|---|---|
| AdExchanger | `https://adexchanger.com/feed/` |
| Digiday | `https://digiday.com/feed/` |
| Ad Tech Daily | `https://adtechdaily.com/feed/` |
| PPC Land | `https://ppc.land/feed/` |
| Marketing Dive | `https://www.marketingdive.com/topic/marketing-technology/feed/` |
| IAB Tech Lab | `https://iabtechlab.com/feed/` |

Articles are filtered by 17 adtech/programmatic keywords before inclusion. Maximum 15 articles total, sorted by recency.

---

## Pipeline Stages

### Stage 1 — Subscriber fetch

Queries PostgreSQL for active subscribers with valid GDPR consent. Hard requirement: `consent_newsletter = TRUE` and `withdrawn_at IS NULL`. Pipeline aborts gracefully if zero subscribers.

### Stage 2 — Research Agent

Runs three parallel async tasks:
- GitHub API calls for protocol version data (with Bearer token auth)
- NewsAPI query (3 queries in sequence to stay within free-tier rate limits)
- RSS feed fetches (6 concurrent)

Returns a structured research dict:
```python
{
  "protocols": {
    "adcp": {"version": "v2.5.1", "tag": "v2.5.1"},
    "mcp": {"version": "2025-11-25", "tag": "2025-11-25"},
    ...
  },
  "news": [
    {"title": "...", "source": "AdExchanger", "url": "...", "published": "..."},
    ...
  ],
  "community": []
}
```

### Stage 3 — Content Agent (Claude)

Sends the research data to Claude Sonnet 4 with a structured system prompt requesting JSON output. The prompt instructs Claude to:
- Write a subject line anchored in the most significant protocol development of the week
- Draft a lead story (2–3 paragraphs) on the highest-signal protocol event
- Summarise the top 3 news items
- Note protocol version changes
- Keep the tone direct and commercially grounded — no marketing language

JSON parse is protected by a markdown fence stripper and one automatic retry on failure.

### Stage 4 — Compliance Agent

Runs 11 hard checks before any send:

| Check | Required |
|---|---|
| Unsubscribe link present | ✅ |
| Privacy policy link present | ✅ |
| GDPR consent ID in footer | ✅ |
| Legal footer block present | ✅ |
| Sender address is verified | ✅ |
| No tracking pixels without consent | ✅ |
| CNIL reference present | ✅ |
| DPO contact present | ✅ |
| List-Unsubscribe header declared | ✅ |
| Subject line present and non-empty | ✅ |
| HTML is valid UTF-8 | ✅ |

If any check fails, the pipeline stops and sends an internal alert email. No newsletter is dispatched with a compliance failure.

### Stage 5 — Send Agent

For each active subscriber:
1. Generates a signed, per-subscriber unsubscribe token (HMAC-SHA256)
2. Personalises the HTML with first name and consent ID
3. Dispatches via Mailgun API (POST `/v3/{domain}/messages`)
4. Logs send status to `newsletter_send_log`

All sends use Mailgun batch dispatch with `recipient-variables` for personalisation — one API call per issue regardless of subscriber count.

---

## Database Schema

### newsletter_subscribers

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `email` | VARCHAR(255) | Unique |
| `first_name` | VARCHAR(100) | |
| `role` | VARCHAR(100) | Agency / Brand / Publisher etc. |
| `status` | VARCHAR(20) | `active`, `unsubscribed`, `bounced`, `complained` |
| `created_at` | TIMESTAMPTZ | |

### newsletter_consent (GDPR audit trail)

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key — used as consent ID in emails |
| `subscriber_id` | UUID | FK → newsletter_subscribers |
| `consent_newsletter` | BOOLEAN | Required TRUE to receive email |
| `consent_privacy` | BOOLEAN | Must be TRUE at signup |
| `consent_date` | TIMESTAMPTZ | Timestamp of consent |
| `consent_ip` | INET | IP address at consent |
| `consent_source` | VARCHAR(200) | e.g. `pievra.com/newsletter` |
| `gdpr_basis` | VARCHAR(50) | `consent_art6_1a` |
| `withdrawn_at` | TIMESTAMPTZ | Set on unsubscribe |
| `withdrawal_method` | VARCHAR(100) | `unsubscribe_link` |

### newsletter_issues

| Column | Type | Notes |
|---|---|---|
| `issue_number` | INTEGER | Unique, sequential |
| `subject` | VARCHAR(200) | Email subject line |
| `run_id` | VARCHAR(100) | Pipeline run identifier |
| `sent_at` | TIMESTAMPTZ | |
| `subscriber_count` | INTEGER | At time of send |
| `sent_count` | INTEGER | Successful dispatches |
| `dry_run` | BOOLEAN | TRUE = built but not sent |

---

## Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key (Sonnet 4) |
| `EMAIL_PROVIDER` | `mailgun` or `sendgrid` |
| `EMAIL_API_KEY` | Mailgun / SendGrid API key |
| `EMAIL_FROM` | Verified sender address |
| `EMAIL_DOMAIN` | Verified sending domain |
| `DATABASE_URL` | PostgreSQL connection string |
| `GITHUB_TOKEN` | Personal access token (`public_repo` scope) |
| `NEWS_API_KEY` | NewsAPI.org key |
| `UNSUBSCRIBE_SECRET` | 32-char hex string for HMAC token signing |
| `ALERT_EMAIL` | Internal address for pipeline failure alerts |

---

## Running the Pipeline

```bash
# Activate environment
cd /opt/pievra-newsletter
source venv/bin/activate
set -a && source .env && set +a

# Dry run — builds newsletter but does NOT send
python orchestrator.py --dry-run --force

# Force run on any day (bypasses Tuesday check)
python orchestrator.py --force

# Normal run (only executes on Tuesdays)
python orchestrator.py
```

### Cron schedule

```
# Pievra Newsletter — Every Tuesday at 05:00 UTC (06:00 CET)
0 5 * * 2 /opt/pievra-newsletter/run.sh
```

---

## GDPR Compliance

The newsletter pipeline is designed for GDPR Art.6(1)(a) — consent basis.

- Consent is collected at subscription with timestamp and IP recorded
- Every email contains a one-click unsubscribe link (GDPR Art.7(3))
- Unsubscribe records the withdrawal timestamp in `newsletter_consent.withdrawn_at`
- No email is ever sent to a subscriber with `withdrawn_at IS NOT NULL`
- Consent ID is included in every email footer for audit purposes
- CNIL (French data protection authority) compliance for EU/France subscribers

---

## Monitoring

Pipeline runs log to `/var/log/pievra-newsletter.log`.

Check the last run:
```bash
tail -50 /var/log/pievra-newsletter.log
```

Check issue history in PostgreSQL:
```sql
SELECT issue_number, subject, sent_at, subscriber_count, sent_count
FROM newsletter_issues
ORDER BY sent_at DESC
LIMIT 10;
```
