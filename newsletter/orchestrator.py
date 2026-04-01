"""
Pievra Protocol Intelligence Weekly - Newsletter Orchestrator Agent
===================================================================
Runs every Tuesday at 06:00 CET via cron / cloud scheduler.
Coordinates four sub-agents:
  1. ResearchAgent     - fetches latest protocol news and version data
  2. ContentAgent      - drafts the newsletter body using Claude API
  3. ComplianceAgent   - validates GDPR legal footers and consent compliance
  4. SendAgent         - renders HTML and dispatches via email service

Architecture:
  orchestrator.py (this file)
    └── agents/research_agent.py
    └── agents/content_agent.py
    └── agents/compliance_agent.py
    └── agents/send_agent.py
    └── templates/newsletter_template.html
    └── config/settings.py
    └── db/subscribers.py

Environment variables required:
  ANTHROPIC_API_KEY      - Claude API key
  EMAIL_API_KEY          - Mailgun / SendGrid API key
  EMAIL_FROM             - newsletter@pievra.com
  EMAIL_DOMAIN           - mg.pievra.com (Mailgun) or verified SendGrid domain
  DATABASE_URL           - PostgreSQL connection string for subscriber/consent DB
  GITHUB_TOKEN           - For fetching AdCP/ARTF/MCP repo data
  PIEVRA_API_KEY         - Internal Pievra API for marketplace/leaderboard data
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from agents.research_agent import ResearchAgent
from agents.content_agent import ContentAgent
from agents.compliance_agent import ComplianceAgent
from agents.send_agent import SendAgent
from db.subscribers import SubscriberDB
from config.settings import Settings

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("orchestrator")

CET = ZoneInfo("Europe/Paris")


class NewsletterOrchestrator:
    """
    Master agent that coordinates the weekly newsletter pipeline.
    Called every Tuesday at 06:00 CET by the scheduler.
    """

    def __init__(self):
        self.settings = Settings()
        self.db = SubscriberDB(self.settings.DATABASE_URL)
        self.research_agent = ResearchAgent(self.settings)
        self.content_agent = ContentAgent(self.settings)
        self.compliance_agent = ComplianceAgent(self.settings)
        self.send_agent = SendAgent(self.settings)
        self.issue_number = None
        self.run_id = f"run_{datetime.now(CET).strftime('%Y%m%d_%H%M%S')}"

    async def run(self, dry_run: bool = False) -> dict:
        """
        Full pipeline. Returns a run summary dict.
        dry_run=True: builds newsletter but does NOT send.
        """
        start = datetime.now(CET)
        log.info(f"🐙 Pievra Newsletter Orchestrator starting - run_id={self.run_id}")

        summary = {
            "run_id": self.run_id,
            "started_at": start.isoformat(),
            "dry_run": dry_run,
            "stages": {},
            "errors": [],
            "subscriber_count": 0,
            "sent_count": 0,
        }

        try:
            # ── STAGE 1: Get active subscribers ─────────────────────────────
            log.info("Stage 1/5: Fetching active subscribers")
            subscribers = await self.db.get_active_subscribers()
            summary["subscriber_count"] = len(subscribers)
            summary["stages"]["subscribers"] = {
                "status": "ok", "count": len(subscribers)
            }
            log.info(f"  ✓ {len(subscribers)} active subscribers with valid consent")

            if not subscribers and not dry_run:
                log.warning("No subscribers - aborting send")
                return summary

            # ── STAGE 2: Research - gather protocol intelligence ─────────────
            log.info("Stage 2/5: Research Agent - gathering protocol data")
            research_data = await self.research_agent.gather()
            summary["stages"]["research"] = {
                "status": "ok",
                "protocols_tracked": len(research_data.get("protocols", {})),
                "news_items": len(research_data.get("news", [])),
                "community_highlights": len(research_data.get("community", [])),
            }
            log.info(f"  ✓ Research complete: {summary['stages']['research']}")

            # ── STAGE 3: Content - draft newsletter with Claude ──────────────
            log.info("Stage 3/5: Content Agent - drafting newsletter with Claude API")
            self.issue_number = await self.db.get_next_issue_number()
            newsletter = await self.content_agent.draft(
                research_data=research_data,
                issue_number=self.issue_number,
                send_date=start,
            )
            summary["stages"]["content"] = {
                "status": "ok",
                "issue_number": self.issue_number,
                "subject": newsletter.get("subject"),
                "word_count": newsletter.get("word_count", 0),
            }
            log.info(f"  ✓ Content drafted: issue #{self.issue_number} - \"{newsletter['subject']}\"")

            # ── STAGE 4: Compliance - validate GDPR legal content ────────────
            log.info("Stage 4/5: Compliance Agent - GDPR and legal validation")
            compliance_result = await self.compliance_agent.validate(newsletter)
            if not compliance_result["passed"]:
                errors = compliance_result.get("errors", [])
                log.error(f"  ✗ Compliance FAILED: {errors}")
                summary["errors"].extend(errors)
                summary["stages"]["compliance"] = {"status": "failed", "errors": errors}
                raise ValueError(f"Compliance validation failed: {errors}")
            summary["stages"]["compliance"] = {
                "status": "ok",
                "checks_passed": compliance_result.get("checks_passed", 0),
                "legal_footer_present": compliance_result.get("legal_footer_present"),
                "unsubscribe_link_present": compliance_result.get("unsubscribe_link_present"),
                "consent_id_present": compliance_result.get("consent_id_present"),
            }
            log.info(f"  ✓ Compliance OK: {compliance_result['checks_passed']} checks passed")

            # ── STAGE 5: Send ────────────────────────────────────────────────
            if dry_run:
                log.info("Stage 5/5: DRY RUN - newsletter built but NOT sent")
                summary["stages"]["send"] = {"status": "dry_run", "sent": 0}
            else:
                log.info(f"Stage 5/5: Send Agent - dispatching to {len(subscribers)} subscribers")
                send_result = await self.send_agent.dispatch(
                    newsletter=newsletter,
                    subscribers=subscribers,
                    issue_number=self.issue_number,
                    run_id=self.run_id,
                )
                summary["sent_count"] = send_result.get("sent", 0)
                summary["stages"]["send"] = {
                    "status": "ok",
                    "sent": send_result.get("sent", 0),
                    "failed": send_result.get("failed", 0),
                    "provider_message_id": send_result.get("message_id"),
                }
                log.info(f"  ✓ Sent to {send_result.get('sent')} subscribers")

            # ── Record run in DB ─────────────────────────────────────────────
            await self.db.record_issue_sent(
                issue_number=self.issue_number,
                run_id=self.run_id,
                subject=newsletter.get("subject", ""),
                subscriber_count=len(subscribers),
                sent_count=summary.get("sent_count", 0),
                dry_run=dry_run,
            )

        except Exception as e:
            log.exception(f"Orchestrator error: {e}")
            summary["errors"].append(str(e))
            summary["status"] = "failed"
            # Alert on failure
            await self._alert_failure(str(e), summary)
            return summary

        elapsed = (datetime.now(CET) - start).total_seconds()
        summary["elapsed_seconds"] = round(elapsed, 2)
        summary["status"] = "success"
        log.info(f"🐙 Pipeline complete in {elapsed:.1f}s - {summary['sent_count']} emails sent")
        return summary

    async def _alert_failure(self, error: str, summary: dict):
        """Send an internal alert email on pipeline failure."""
        try:
            await self.send_agent.send_internal_alert(
                subject=f"[ALERT] Newsletter pipeline failed - run_id={self.run_id}",
                body=f"Error: {error}\n\nSummary: {summary}",
                to=self.settings.ALERT_EMAIL,
            )
        except Exception:
            log.exception("Failed to send alert email")


# ── Entry point ────────────────────────────────────────────────────────────────
async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pievra Newsletter Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="Build but do not send")
    parser.add_argument("--force", action="store_true", help="Run even if not Tuesday")
    args = parser.parse_args()

    now = datetime.now(CET)
    if not args.force and now.weekday() != 1:  # 1 = Tuesday
        log.info(f"Today is {now.strftime('%A')} - newsletter only runs on Tuesdays. Use --force to override.")
        return

    orchestrator = NewsletterOrchestrator()
    summary = await orchestrator.run(dry_run=args.dry_run)

    if summary.get("status") == "success":
        log.info("✅ Newsletter pipeline succeeded")
        sys.exit(0)
    else:
        log.error(f"❌ Newsletter pipeline failed: {summary.get('errors')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
