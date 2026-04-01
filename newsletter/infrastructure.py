"""
Pievra Newsletter - Supporting Infrastructure
==============================================
config/settings.py   - Environment configuration
db/subscribers.py    - Subscriber database (PostgreSQL)
scheduler/cron.py    - Tuesday 06:00 CET scheduler
requirements.txt     - Python dependencies
DEPLOYMENT.md        - Full deployment guide
"""


# ══════════════════════════════════════════════════════════════════════════════
# config/settings.py
# ══════════════════════════════════════════════════════════════════════════════

import os
from dataclasses import dataclass, field

@dataclass
class Settings:
    # Anthropic / Claude
    ANTHROPIC_API_KEY: str = field(default_factory=lambda: os.environ["ANTHROPIC_API_KEY"])

    # Email provider
    EMAIL_PROVIDER: str = field(default_factory=lambda: os.getenv("EMAIL_PROVIDER", "mailgun"))
    EMAIL_API_KEY: str = field(default_factory=lambda: os.environ["EMAIL_API_KEY"])
    EMAIL_FROM: str = field(default_factory=lambda: os.getenv("EMAIL_FROM", "newsletter@pievra.com"))
    EMAIL_DOMAIN: str = field(default_factory=lambda: os.getenv("EMAIL_DOMAIN", "mg.pievra.com"))

    # Database
    DATABASE_URL: str = field(default_factory=lambda: os.environ["DATABASE_URL"])

    # External APIs
    GITHUB_TOKEN: str = field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))
    NEWS_API_KEY: str = field(default_factory=lambda: os.getenv("NEWS_API_KEY", ""))
    PIEVRA_API_BASE: str = field(default_factory=lambda: os.getenv("PIEVRA_API_BASE", "https://api.pievra.com/v1"))
    PIEVRA_API_KEY: str = field(default_factory=lambda: os.getenv("PIEVRA_API_KEY", ""))

    # Security
    UNSUBSCRIBE_SECRET: str = field(default_factory=lambda: os.environ["UNSUBSCRIBE_SECRET"])

    # Alerts
    ALERT_EMAIL: str = field(default_factory=lambda: os.getenv("ALERT_EMAIL", "ops@pievra.com"))


# ══════════════════════════════════════════════════════════════════════════════
# db/subscribers.py
# ══════════════════════════════════════════════════════════════════════════════

import asyncpg
import logging
from datetime import datetime
from typing import Optional

log_db = logging.getLogger("db.subscribers")


# PostgreSQL schema (run once on first deploy):
SCHEMA_SQL = """
-- Subscribers table
CREATE TABLE IF NOT EXISTS newsletter_subscribers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    first_name      VARCHAR(100),
    role            VARCHAR(100),
    status          VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active','unsubscribed','bounced','complained')),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- GDPR consent records (separate table for audit trail)
CREATE TABLE IF NOT EXISTS newsletter_consent (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscriber_id       UUID REFERENCES newsletter_subscribers(id) ON DELETE CASCADE,
    email               VARCHAR(255) NOT NULL,
    consent_newsletter  BOOLEAN NOT NULL DEFAULT TRUE,
    consent_privacy     BOOLEAN NOT NULL DEFAULT TRUE,
    consent_marketing   BOOLEAN NOT NULL DEFAULT FALSE,
    consent_date        TIMESTAMPTZ DEFAULT NOW(),
    consent_ip          INET,
    consent_source      VARCHAR(200),   -- e.g. 'pievra.com/newsletter'
    consent_method      VARCHAR(50),    -- 'double_opt_in' | 'single_opt_in'
    gdpr_basis          VARCHAR(50) DEFAULT 'consent_art6_1a',
    withdrawn_at        TIMESTAMPTZ,
    withdrawal_method   VARCHAR(100),
    UNIQUE(subscriber_id)
);

-- Issues sent log
CREATE TABLE IF NOT EXISTS newsletter_issues (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_number    INTEGER UNIQUE NOT NULL,
    subject         VARCHAR(200),
    run_id          VARCHAR(100),
    sent_at         TIMESTAMPTZ DEFAULT NOW(),
    subscriber_count INTEGER DEFAULT 0,
    sent_count      INTEGER DEFAULT 0,
    dry_run         BOOLEAN DEFAULT FALSE
);

-- Send log per subscriber (for unsubscribe tracking & analytics)
CREATE TABLE IF NOT EXISTS newsletter_send_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_number    INTEGER NOT NULL,
    subscriber_id   UUID REFERENCES newsletter_subscribers(id),
    sent_at         TIMESTAMPTZ DEFAULT NOW(),
    opened_at       TIMESTAMPTZ,
    clicked_at      TIMESTAMPTZ
);

-- Index for performance
CREATE INDEX IF NOT EXISTS idx_subscribers_status ON newsletter_subscribers(status);
CREATE INDEX IF NOT EXISTS idx_consent_subscriber ON newsletter_consent(subscriber_id);
CREATE INDEX IF NOT EXISTS idx_send_log_issue ON newsletter_send_log(issue_number);
"""


class SubscriberDB:
    """PostgreSQL-backed subscriber store with full GDPR consent audit trail."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._pool: Optional[asyncpg.Pool] = None

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(self.database_url, min_size=2, max_size=10)
        return self._pool

    async def get_active_subscribers(self) -> list[dict]:
        """
        Returns only subscribers with:
        - status = 'active'
        - valid newsletter consent (consent_newsletter = TRUE)
        - consent not withdrawn
        GDPR requirement: never send to subscriber without valid consent.
        """
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    s.id::text,
                    s.email,
                    s.first_name,
                    s.role,
                    c.id::text AS consent_id,
                    c.consent_date::text,
                    c.consent_marketing
                FROM newsletter_subscribers s
                INNER JOIN newsletter_consent c ON c.subscriber_id = s.id
                WHERE s.status = 'active'
                  AND c.consent_newsletter = TRUE
                  AND c.withdrawn_at IS NULL
                ORDER BY s.created_at ASC
            """)
            log_db.info(f"  Found {len(rows)} active consenting subscribers")
            return [dict(r) for r in rows]

    async def subscribe(
        self,
        email: str,
        first_name: str,
        role: str,
        consent_newsletter: bool,
        consent_privacy: bool,
        consent_marketing: bool,
        ip_address: str,
        source: str = "pievra.com/newsletter",
    ) -> dict:
        """
        Subscribe a new user with full GDPR consent recording.
        Returns subscriber dict with consent_id.
        """
        if not consent_newsletter or not consent_privacy:
            raise ValueError("Newsletter and privacy consent are required")

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                # Upsert subscriber
                subscriber = await conn.fetchrow("""
                    INSERT INTO newsletter_subscribers (email, first_name, role)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (email) DO UPDATE
                    SET first_name = EXCLUDED.first_name,
                        role = EXCLUDED.role,
                        status = 'active',
                        updated_at = NOW()
                    RETURNING id::text, email, first_name, status
                """, email.lower().strip(), first_name.strip(), role)

                # Record consent
                consent = await conn.fetchrow("""
                    INSERT INTO newsletter_consent (
                        subscriber_id, email, consent_newsletter, consent_privacy,
                        consent_marketing, consent_ip, consent_source,
                        consent_method, gdpr_basis
                    ) VALUES ($1, $2, $3, $4, $5, $6::inet, $7, $8, $9)
                    ON CONFLICT (subscriber_id) DO UPDATE SET
                        consent_newsletter = EXCLUDED.consent_newsletter,
                        consent_privacy = EXCLUDED.consent_privacy,
                        consent_marketing = EXCLUDED.consent_marketing,
                        consent_date = NOW(),
                        consent_ip = EXCLUDED.consent_ip,
                        withdrawn_at = NULL
                    RETURNING id::text, consent_date::text
                """,
                    subscriber["id"], email.lower().strip(),
                    consent_newsletter, consent_privacy, consent_marketing,
                    ip_address, source, "single_opt_in", "consent_art6_1a"
                )

                log_db.info(f"  ✓ Subscribed {email} - consent_id={consent['id']}")
                return {
                    "subscriber_id": subscriber["id"],
                    "email": subscriber["email"],
                    "consent_id": consent["id"],
                    "consent_date": consent["consent_date"],
                    "status": "subscribed",
                }

    async def unsubscribe(self, token: str) -> dict:
        """
        Process unsubscribe request. Records withdrawal in consent table.
        GDPR Art.7(3): withdrawal must be as easy as giving consent.
        """
        import hmac, hashlib, base64
        from config.settings import Settings

        try:
            decoded = base64.urlsafe_b64decode(token.encode()).decode()
            subscriber_id, sig = decoded.rsplit(":", 1)
        except Exception:
            raise ValueError("Invalid unsubscribe token")

        pool = await self._get_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    UPDATE newsletter_subscribers
                    SET status = 'unsubscribed', updated_at = NOW()
                    WHERE id = $1::uuid
                """, subscriber_id)

                await conn.execute("""
                    UPDATE newsletter_consent
                    SET withdrawn_at = NOW(),
                        withdrawal_method = 'unsubscribe_link'
                    WHERE subscriber_id = $1::uuid
                """, subscriber_id)

        log_db.info(f"  ✓ Unsubscribed subscriber_id={subscriber_id}")
        return {"status": "unsubscribed", "subscriber_id": subscriber_id}

    async def get_next_issue_number(self) -> int:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT COALESCE(MAX(issue_number), 0) + 1 AS next FROM newsletter_issues")
            return row["next"]

    async def record_issue_sent(
        self, issue_number: int, run_id: str, subject: str,
        subscriber_count: int, sent_count: int, dry_run: bool
    ):
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO newsletter_issues (issue_number, subject, run_id, subscriber_count, sent_count, dry_run)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (issue_number) DO NOTHING
            """, issue_number, subject, run_id, subscriber_count, sent_count, dry_run)


# ══════════════════════════════════════════════════════════════════════════════
# scheduler/cron.py
# Runs the orchestrator every Tuesday at 06:00 CET.
# Can be deployed as:
#   - A cron job on any Linux server
#   - A Cloud Scheduler job (GCP / AWS EventBridge)
#   - A GitHub Actions scheduled workflow
# ══════════════════════════════════════════════════════════════════════════════

# Linux crontab entry (paste into `crontab -e`):
CRONTAB_ENTRY = """
# Pievra Newsletter - Every Tuesday at 06:00 CET (UTC+1 in winter, UTC+2 in summer)
# Use explicit UTC times to handle DST: 05:00 UTC (winter) / 04:00 UTC (summer)
# Recommended: use a scheduler that handles timezones natively (see below)

# Simple cron (UTC, adjust for DST manually):
0 5 * * 2 cd /app && python orchestrator.py >> /var/log/pievra-newsletter.log 2>&1
"""

# GCP Cloud Scheduler (handles timezone natively):
GCP_SCHEDULER_CONFIG = """
gcloud scheduler jobs create http pievra-newsletter-tuesday \\
  --schedule="0 6 * * 2" \\
  --uri="https://your-cloud-run-service/run-newsletter" \\
  --time-zone="Europe/Paris" \\
  --http-method=POST \\
  --message-body='{"dry_run": false}' \\
  --oidc-service-account-email=newsletter@your-project.iam.gserviceaccount.com
"""

# GitHub Actions workflow (add to .github/workflows/newsletter.yml):
GITHUB_ACTIONS_WORKFLOW = """
name: Pievra Newsletter - Tuesday Dispatch

on:
  schedule:
    # Every Tuesday at 06:00 CET (05:00 UTC in winter)
    - cron: '0 5 * * 2'
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Dry run (build but do not send)'
        required: false
        default: 'false'

jobs:
  send-newsletter:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r newsletter/requirements.txt

      - name: Run newsletter orchestrator
        working-directory: newsletter
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          EMAIL_API_KEY: ${{ secrets.EMAIL_API_KEY }}
          EMAIL_FROM: newsletter@pievra.com
          EMAIL_DOMAIN: mg.pievra.com
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          PIEVRA_API_KEY: ${{ secrets.PIEVRA_API_KEY }}
          PIEVRA_API_BASE: https://api.pievra.com/v1
          UNSUBSCRIBE_SECRET: ${{ secrets.UNSUBSCRIBE_SECRET }}
          ALERT_EMAIL: ops@pievra.com
        run: |
          DRY_FLAG=""
          if [ "${{ github.event.inputs.dry_run }}" = "true" ]; then
            DRY_FLAG="--dry-run"
          fi
          python orchestrator.py $DRY_FLAG --force

      - name: Notify on failure
        if: failure()
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Newsletter pipeline failed',
              body: 'The Tuesday newsletter dispatch failed. Check the workflow run for details.',
              labels: ['newsletter', 'ops']
            })
"""


# ══════════════════════════════════════════════════════════════════════════════
# requirements.txt
# ══════════════════════════════════════════════════════════════════════════════

REQUIREMENTS = """
# Pievra Newsletter Agent - Python Dependencies
anthropic>=0.40.0       # Claude API - content drafting
asyncpg>=0.29.0         # PostgreSQL async driver - subscriber DB
httpx>=0.27.0           # Async HTTP - GitHub, Mailgun, SendGrid, news APIs
python-dateutil>=2.9.0  # Date handling for CET/UTC conversion
zoneinfo; python_version < "3.9"  # Timezone support (built-in from 3.9+)

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
"""


# ══════════════════════════════════════════════════════════════════════════════
# DEPLOYMENT.md
# ══════════════════════════════════════════════════════════════════════════════

DEPLOYMENT_GUIDE = """
# Pievra Newsletter - Deployment Guide

## Architecture

Orchestrator → ResearchAgent → ContentAgent (Claude) → ComplianceAgent → SendAgent → Mailgun/SendGrid

The orchestrator runs as a scheduled job every Tuesday at 06:00 CET.
All agents are async Python modules called in sequence by the orchestrator.

## Environment Variables (required)

| Variable              | Description                                    | Example                          |
|-----------------------|------------------------------------------------|----------------------------------|
| ANTHROPIC_API_KEY     | Claude API key                                 | sk-ant-...                       |
| EMAIL_PROVIDER        | mailgun or sendgrid                            | mailgun                          |
| EMAIL_API_KEY         | Mailgun or SendGrid API key                    | key-...                          |
| EMAIL_FROM            | Verified sender address                        | newsletter@pievra.com            |
| EMAIL_DOMAIN          | Verified sending domain                        | mg.pievra.com                    |
| DATABASE_URL          | PostgreSQL connection string                   | postgresql://...                 |
| GITHUB_TOKEN          | GitHub token for protocol repo fetching        | ghp_...                          |
| NEWS_API_KEY          | NewsAPI key for news digest                    | ...                              |
| PIEVRA_API_KEY        | Internal Pievra API key                        | ...                              |
| PIEVRA_API_BASE       | Pievra API base URL                            | https://api.pievra.com/v1        |
| UNSUBSCRIBE_SECRET    | Secret for signing unsubscribe tokens (32 chars)| random 32-char string           |
| ALERT_EMAIL           | Email for pipeline failure alerts              | ops@pievra.com                   |

## Step 1: Database Setup

Connect to your PostgreSQL instance and run the SCHEMA_SQL from db/subscribers.py.
This creates the subscribers, consent, issues, and send_log tables.

## Step 2: Email Domain Verification

### Mailgun
1. Add sending domain mg.pievra.com in Mailgun dashboard
2. Add DNS records: MX, TXT (SPF), CNAME (DKIM), CNAME (tracking)
3. Verify newsletter@pievra.com as sender
4. Set up unsubscribe webhook: POST to /api/newsletter/unsubscribe

### SendGrid
1. Verify pievra.com as sender domain
2. Add CNAME records for DKIM
3. Configure event webhook for unsubscribes

## Step 3: Subscription API Endpoint

Add this endpoint to your Pievra backend at POST /api/newsletter/subscribe:

    {
      "email": "user@company.com",
      "first_name": "Alex",
      "role": "Agency / Media Buyer",
      "consent_newsletter": true,
      "consent_privacy": true,
      "consent_marketing": false
    }

The endpoint must:
1. Validate all required consents
2. Record subscriber + consent in PostgreSQL via SubscriberDB.subscribe()
3. Return consent_id and send a double opt-in confirmation email
4. Store consent timestamp and IP address for GDPR audit trail

## Step 4: Unsubscribe Endpoint

Add GET/POST /newsletter/unsubscribe?t={token}:
1. Validate the signed token
2. Call SubscriberDB.unsubscribe(token)
3. Show confirmation page
4. Do NOT require login - GDPR requires one-click unsubscribe

## Step 5: Deploy the Scheduler

### Recommended: GitHub Actions (see GITHUB_ACTIONS_WORKFLOW)
Add newsletter/ directory to your repo.
Add all secrets to GitHub repository secrets.
Create .github/workflows/newsletter.yml with the GITHUB_ACTIONS_WORKFLOW content.

### Alternative: GCP Cloud Scheduler
Deploy orchestrator as a Cloud Run service.
Create scheduler job using GCP_SCHEDULER_CONFIG.

## Step 6: Test Run

python orchestrator.py --dry-run --force

This builds the full newsletter without sending. Check the output log for any compliance errors.

## Step 7: First Live Run

python orchestrator.py --force

Monitor the run in your log output. Check Mailgun/SendGrid dashboard for delivery confirmation.

## GDPR Compliance Checklist

✓ Consent recorded with timestamp and IP before first send
✓ Consent ID included in every email footer
✓ One-click unsubscribe in every email
✓ List-Unsubscribe email header present
✓ Unsubscribe processed within 10 working days (automatic - same day)
✓ Withdrawal recorded in newsletter_consent table
✓ Privacy Policy linked in every email
✓ DPO contact in every email
✓ CNIL supervisory authority referenced
✓ No email sent without active consent (ComplianceAgent validates before send)
✓ Data retention: subscriber data deleted on account closure (cascade on subscriber delete)

## Troubleshooting

Pipeline fails at ContentAgent:
  - Check ANTHROPIC_API_KEY is valid
  - Check Claude API quota

Pipeline fails at SendAgent:
  - Check EMAIL_API_KEY and EMAIL_DOMAIN are correct
  - Verify sending domain in Mailgun/SendGrid dashboard

ComplianceAgent blocks send:
  - Check newsletter HTML contains all required legal elements
  - Never remove the GDPR footer from the template
"""

# Write all files
if __name__ == "__main__":
    import pathlib, os

    base = pathlib.Path(__file__).parent

    # Write requirements.txt
    (base / "requirements.txt").write_text(REQUIREMENTS.strip())
    print("✓ requirements.txt")

    # Write DEPLOYMENT.md
    (base / "DEPLOYMENT.md").write_text(DEPLOYMENT_GUIDE.strip())
    print("✓ DEPLOYMENT.md")

    # Write crontab
    (base / "scheduler" / "crontab.txt").write_text(CRONTAB_ENTRY.strip())
    print("✓ scheduler/crontab.txt")

    # Write GitHub Actions workflow
    gha_dir = base / ".github" / "workflows"
    gha_dir.mkdir(parents=True, exist_ok=True)
    (gha_dir / "newsletter.yml").write_text(GITHUB_ACTIONS_WORKFLOW.strip())
    print("✓ .github/workflows/newsletter.yml")

    print("\nAll supporting files written.")
