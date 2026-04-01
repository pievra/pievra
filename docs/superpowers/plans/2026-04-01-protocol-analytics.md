# Protocol Analytics Dashboard - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a data-driven protocol analytics page at `/news/analytics` that auto-collects adoption metrics (GitHub, npm, PyPI, registries) daily, shows real-time rankings, trend charts, geographic deployment data, and a searchable company directory.

**Architecture:** Python collector agent (daily cron) stores metrics in SQLite. Next.js page reads from SQLite, with 1h-cached real-time refresh for key metrics. Recharts for client-side charts. Extends existing pievra-news Next.js app.

**Tech Stack:** Python 3 (httpx, sqlite3), Next.js 16, Recharts, Tailwind CSS, SQLite

**Spec:** `docs/superpowers/specs/2026-04-01-protocol-analytics-design.md`

---

## Verified Data Sources

| Protocol | GitHub Repo (primary) | npm Package | PyPI Package |
|----------|----------------------|-------------|-------------|
| MCP | modelcontextprotocol/modelcontextprotocol | @modelcontextprotocol/sdk | mcp |
| AdCP | adcontextprotocol/adcp | @adcp/client | - |
| A2A | a2aproject/A2A | - | - |
| ARTF | IABTechLab/agentic-rtb-framework | - | - |
| Agentic Audiences | IABTechLab/agentic-audiences | - | - |

---

## Task 1: Analytics Database Schema + Python Config + TS Queries

Create the foundation: Python config with protocol definitions, geocoder utility, SQLite schema, and TypeScript query module.

**Files:**
- Create: `/opt/pievra-analytics/config.py` (protocol definitions with GitHub repos, npm/PyPI packages, maturity status)
- Create: `/opt/pievra-analytics/geocoder.py` (location string to ISO country code mapping + country to region mapping)
- Create: `/var/www/pievra-news/src/lib/analytics-db.ts` (SQLite connection, migrations for 5 tables: protocol_metrics, protocol_packages, deployments, contributor_locations, metrics_cache; query functions: getLatestMetrics, getMetricsTrend, getDeployments, getCountryStats, getCategoryStats, getProtocolOverlap, getCachedMetric, setCachedMetric)

Tables: protocol_metrics (daily snapshots with stars/forks/contributors/downloads per protocol), deployments (company/protocol/country/category/source), contributor_locations (GitHub user locations), metrics_cache (1h TTL key-value cache).

---

## Task 2: Python Collector Agent

Create the daily data collection script.

**Files:**
- Create: `/opt/pievra-analytics/collector.py`

Collection steps per protocol:
1. GitHub REST API: stars, forks, open_issues from `/repos/{owner}/{repo}`. Contributors count via paginated Link header. Commits in 30 days via paginated count.
2. npm API: `https://api.npmjs.org/downloads/point/last-week/{package}` for each npm package.
3. PyPI API: `https://pypistats.org/api/packages/{package}/recent` for each PyPI package.
4. Store one row per protocol in protocol_metrics for today's date.

Uses httpx with timeout=15. GITHUB_TOKEN env var for auth. Graceful degradation on errors. Entry point: `run()`.

Set up cron: `0 4 * * *` with flock.

---

## Task 3: Seed Deployment Directory

Create and run a seed script with known protocol adopters.

**Files:**
- Create: `/opt/pievra-analytics/seed_deployments.py`

Seed data: AdCP founding members (16+ companies), MCP ecosystem (Anthropic, OpenAI, Google, Block, etc.), A2A ecosystem (Google, Salesforce, SAP), ARTF reference implementation, France agentic campaign (PubMatic + Amnet). Each with company, protocol, country, category, source_url, announced_date.

---

## Task 4: Protocol Scorecards Component

**Files:**
- Create: `/var/www/pievra-news/src/components/analytics/protocol-scorecards.tsx`

Install Recharts: `npm install recharts`

5 cards in a row ranked by composite score. Each card: rank badge, protocol name + maturity badge, GitHub stars, downloads/week, contributors, 30-day momentum %, sparkline (Recharts LineChart, 30-day stars, no axes). Protocol colors: MCP=#065f46, AdCP=#1d4ed8, A2A=#5b21b6, ARTF=#9d174d, Agentic Audiences=#92400e.

---

## Task 5: Charts Components

**Files:**
- Create: `/var/www/pievra-news/src/components/analytics/adoption-chart.tsx` ("use client", Recharts LineChart, 5 protocol lines, toggle metric: Stars/Downloads/Contributors/Agents, range: 30d/90d/6m/1y/All, tooltip, responsive)
- Create: `/var/www/pievra-news/src/components/analytics/geo-distribution.tsx` (horizontal BarChart top 10 countries with flag emoji, filter by protocol)
- Create: `/var/www/pievra-news/src/components/analytics/category-breakdown.tsx` (stacked horizontal bars per protocol, colored by category)
- Create: `/var/www/pievra-news/src/components/analytics/protocol-overlap.tsx` (list of multi-protocol companies with protocol badges)

---

## Task 6: Deployment Directory Table Component

**Files:**
- Create: `/var/www/pievra-news/src/components/analytics/deployment-table.tsx`

"use client" component. Search input, filter dropdowns (Protocol, Country, Category), sort (Recent, A-Z). Table: Company, Protocol badges, Country flag+code, Category, Date, Source link. Pagination. Footer with total count. "Submit a deployment" link.

---

## Task 7: Analytics Page + API Routes

**Files:**
- Create: `/var/www/pievra-news/src/app/analytics/page.tsx` (server component, fetches all data, assembles sections 1-3)
- Create: `/var/www/pievra-news/src/app/api/analytics/metrics/route.ts` (GET, real-time GitHub+npm fetch with 1h cache)
- Create: `/var/www/pievra-news/src/app/api/analytics/deployments/route.ts` (GET, filtered/paginated deployments)

Page layout: header, scorecards, trends chart, two-column geo+categories, overlap list, deployment directory. All within max-w-[1200px] mx-auto. SEO metadata.

---

## Task 8: Admin Deployments Panel

**Files:**
- Create: `/var/www/pievra-news/src/app/admin/deployments/page.tsx` (deployment list table with delete)
- Create: `/var/www/pievra-news/src/app/admin/deployments/new/page.tsx` (add deployment form)
- Create: `/var/www/pievra-news/src/app/api/admin/deployments/route.ts` (POST create)
- Create: `/var/www/pievra-news/src/app/api/admin/deployments/[id]/route.ts` (PATCH/DELETE)
- Modify: `/var/www/pievra-news/src/app/admin/layout.tsx` (add Deployments link)

All with admin cookie auth.

---

## Task 9: Deploy + Navigation

Build, restart PM2, run collector once, run seed script, verify page loads at `/news/analytics`. Add link to analytics from the news feed page.

---

## Task Dependencies

| Task | Description | Depends On |
|------|-------------|-----------|
| 1 | Database + config + queries | None |
| 2 | Python collector agent | 1 |
| 3 | Seed deployments | 1 |
| 4 | Scorecards component | 1 |
| 5 | Charts components | 1 |
| 6 | Deployment table | 1 |
| 7 | Analytics page + APIs (assembles 4-6) | 4, 5, 6 |
| 8 | Admin deployments panel | 1 |
| 9 | Deploy | 2, 3, 7, 8 |

**Parallelizable**: Tasks 2, 3, 4, 5, 6, 8 can all run after Task 1. Task 7 assembles 4-6. Task 9 is final.
