# Protocol Analytics Dashboard - Design Spec

**Date**: 2026-04-01
**Status**: Approved

## Overview

A data-driven analytics page on Pievra that tracks adoption and deployment of the 5 agentic advertising protocols (AdCP, MCP, Agentic Audiences/UCP, ARTF, A2A) across countries, regions, use cases, and over time. Auto-updates daily via a Python collector agent, with real-time refresh for key metrics on page load.

Serves three user needs:
1. **Decision-makers**: "Which protocol should I bet on?" (rankings, momentum, maturity)
2. **Strategists**: "What's the state of the market?" (trends, geography, categories)
3. **Practitioners**: "Who is using what?" (searchable deployment directory)

## Goals

1. Position Pievra as the definitive source for protocol adoption intelligence
2. Auto-collect data daily from public sources (GitHub, npm, PyPI, registries, news)
3. Show real-time key metrics on page load (cached 1h)
4. Track geographic adoption via company HQ + GitHub contributor locations + manual news tagging
5. Provide searchable deployment directory with company, protocol, country, use case

## Tech Stack

Same as existing pievra-news app:
- Page: Next.js (new route in `/var/www/pievra-news`)
- Database: SQLite (extend existing or new DB at `~/.pievra-analytics/analytics.db`)
- Data collection: Python agent (new, at `/opt/pievra-analytics/`)
- Styling: Tailwind CSS (existing Pievra design tokens)
- Charts: lightweight client-side library (Chart.js or Recharts)

## Architecture

```
Daily cron (6:00 UTC):
  /opt/pievra-analytics/collector.py
    -> GitHub API (stars, forks, contributors, contributor locations)
    -> npm registry (weekly downloads for SDK packages)
    -> PyPI API (downloads for Python packages)
    -> Registry scraping (AdCP registry, MCP directory, IAB registry, A2A directory)
    -> Store snapshots in SQLite

On page load (Next.js server component):
  -> Read daily snapshots from SQLite (trends, rankings)
  -> Real-time fetch: GitHub stars + npm weekly downloads (cached 1h in SQLite)
  -> Render charts, tables, maps

Admin panel (existing /news/admin):
  -> Add/edit deployment entries (company, protocol, country, use case, source URL)
  -> Tag news articles as deployment signals
```

## Data Model

### protocol_metrics (daily snapshots)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| protocol | TEXT NOT NULL | AdCP, MCP, Agentic Audiences, ARTF, A2A |
| date | TEXT NOT NULL | YYYY-MM-DD |
| github_stars | INTEGER | |
| github_forks | INTEGER | |
| github_contributors | INTEGER | |
| github_open_issues | INTEGER | |
| github_commits_30d | INTEGER | Commits in last 30 days |
| npm_weekly_downloads | INTEGER | Sum across all packages |
| pypi_weekly_downloads | INTEGER | Sum across all packages |
| registered_agents | INTEGER | Count from public registries |
| UNIQUE(protocol, date) | | One row per protocol per day |

### protocol_packages (which packages to track per protocol)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| protocol | TEXT NOT NULL | |
| package_type | TEXT NOT NULL | npm, pypi, github |
| package_name | TEXT NOT NULL | e.g. "@anthropic-ai/mcp-sdk", "adcp-client" |
| github_repo | TEXT | e.g. "modelcontextprotocol/modelcontextprotocol" |
| is_primary | INTEGER DEFAULT 0 | Primary repo for stars/forks counting |

### deployments (who uses what)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| company | TEXT NOT NULL | |
| protocol | TEXT NOT NULL | |
| country | TEXT | ISO 3166-1 alpha-2 (US, FR, DE, etc.) |
| region | TEXT | Derived: North America, Europe, APAC, etc. |
| category | TEXT | Media Trading, Data & Identity, Creative, Infrastructure, Measurement, Retail Media |
| use_case | TEXT | Brief description |
| source_url | TEXT | Press release, GitHub, announcement |
| source_type | TEXT | registry, news, github, manual |
| announced_date | TEXT | When publicly announced |
| created_at | TEXT DEFAULT (datetime('now')) | |

### contributor_locations (GitHub contributor geography)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| protocol | TEXT NOT NULL | |
| github_username | TEXT NOT NULL | |
| location_raw | TEXT | As stated in GitHub profile |
| country | TEXT | Normalized ISO code |
| fetched_at | TEXT | |
| UNIQUE(protocol, github_username) | | |

### metrics_cache (real-time cache)

| Column | Type | Notes |
|--------|------|-------|
| key | TEXT PK | e.g. "github_stars:AdCP", "npm_downloads:MCP" |
| value | TEXT | JSON value |
| cached_at | TEXT | |

## Data Sources Per Protocol

### AdCP
- **GitHub**: `anthropic-ai/ad-context-protocol` (or correct repo from adcontextprotocol.org)
- **npm**: `@adcp/client`, `@adcp/server` (check AdCP docs for exact package names)
- **Registry**: https://adcontextprotocol.org/registry/ (scrape agent count)
- **News**: RSS feed articles tagged with AdCP

### MCP
- **GitHub**: `modelcontextprotocol/modelcontextprotocol`
- **npm**: `@modelcontextprotocol/sdk` (97M+ installs)
- **PyPI**: `mcp`
- **Registry**: MCP server directory (if public API exists)
- **News**: RSS feed articles tagged with MCP

### Agentic Audiences (formerly UCP)
- **GitHub**: `IABTechLab/agentic-audiences` or `IABTechLab/user-context-protocol`
- **npm/pypi**: check if SDKs published
- **Registry**: IAB Tech Lab (if public)
- **News**: RSS feed articles tagged

### ARTF
- **GitHub**: `IABTechLab/agentic-rtb-framework`
- **npm/pypi**: check if SDKs published
- **Registry**: https://artf.ai/ (check for directory)
- **News**: RSS feed articles tagged

### A2A
- **GitHub**: `a2aproject/A2A`
- **npm/pypi**: check for official SDKs
- **Registry**: A2A protocol directory
- **News**: RSS feed articles tagged

**Note**: Exact package names and repo URLs must be verified during implementation. Some may not have published SDKs yet.

## Page Layout

### URL: `/news/analytics` (or `/news/protocols`)

### Section 1: Protocol Rankings ("Which protocol should I bet on?")

```
┌──────────────────────────────────────────────────────────────────┐
│ PROTOCOL INTELLIGENCE                                            │
│ Live adoption metrics across 5 agentic advertising protocols     │
│ Last updated: 2 hours ago                                        │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│ │  MCP    │ │  AdCP   │ │   A2A   │ │  ARTF   │ │ Agentic │   │
│ │ #1      │ │ #2      │ │ #3      │ │ #4      │ │ Aud. #5 │   │
│ │         │ │         │ │         │ │         │ │         │   │
│ │ ⭐ 42K  │ │ ⭐ 3.2K │ │ ⭐ 8.1K │ │ ⭐ 1.8K │ │ ⭐ 920  │   │
│ │ 📦 97M  │ │ 📦 240K │ │ 📦 1.2M │ │ 📦 45K  │ │ 📦 12K  │   │
│ │ 👥 1.2K │ │ 👥 180  │ │ 👥 340  │ │ 👥 95   │ │ 👥 42   │   │
│ │ 🔥 +12% │ │ 🔥 +34% │ │ 🔥 +8%  │ │ 🔥 +22% │ │ 🔥 +15% │   │
│ │ Stable  │ │ Beta    │ │ Stable  │ │ Final   │ │ Draft   │   │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
│                                                                  │
│ Ranked by composite score (stars + downloads + contributors +    │
│ growth rate). Updated daily, key metrics refreshed hourly.       │
└──────────────────────────────────────────────────────────────────┘
```

Each scorecard shows:
- Rank (by composite score)
- GitHub stars (real-time, cached 1h)
- Package downloads/week (npm + PyPI combined)
- Contributors count
- 30-day momentum (% growth in stars + downloads)
- Maturity status badge
- Sparkline (last 30 days trend)

### Section 2: Market Intelligence ("What's the state of the market?")

```
┌──────────────────────────────────────────────────────────────────┐
│ ADOPTION TRENDS                                                  │
│ ┌────────────────────────────────────────────────────┐           │
│ │ [Line chart: 5 protocols over time]                │           │
│ │ X: dates (last 90 days / 6 months / 1 year)       │           │
│ │ Y: GitHub stars (or toggle: downloads, agents)     │           │
│ │ Each protocol = colored line                       │           │
│ └────────────────────────────────────────────────────┘           │
│ Toggle: [Stars] [Downloads] [Contributors] [Agents]              │
│ Range:  [30d] [90d] [6m] [1y] [All]                             │
├──────────────────────────────────────────────────────────────────┤
│ GEOGRAPHIC DISTRIBUTION                                          │
│ ┌──────────────────────┐  ┌──────────────────────────┐          │
│ │ [World map / region   │  │ Top Countries            │          │
│ │  heatmap showing      │  │ 1. US     - 45 deploys   │          │
│ │  deployment density]  │  │ 2. UK     - 12 deploys   │          │
│ │                       │  │ 3. France - 8 deploys    │          │
│ │                       │  │ 4. Germany- 6 deploys    │          │
│ │                       │  │ 5. India  - 5 deploys    │          │
│ └──────────────────────┘  └──────────────────────────┘          │
│ Filter by protocol: [All] [AdCP] [MCP] [AA] [ARTF] [A2A]        │
├──────────────────────────────────────────────────────────────────┤
│ CATEGORY BREAKDOWN                                               │
│ ┌────────────────────────────────────────────────────┐           │
│ │ [Stacked bar chart or donut: deployments by        │           │
│ │  category per protocol]                            │           │
│ │ Media Trading | Data & Identity | Infrastructure   │           │
│ │ Creative | Measurement | Retail Media              │           │
│ └────────────────────────────────────────────────────┘           │
│                                                                  │
│ PROTOCOL OVERLAP                                                 │
│ Companies using multiple protocols:                              │
│ PubMatic: AdCP + MCP + A2A                                       │
│ Yahoo: AdCP + MCP                                                │
│ Optable: AdCP + MCP                                              │
│ ...                                                              │
└──────────────────────────────────────────────────────────────────┘
```

Charts:
- Adoption trends: line chart with toggle for metric (stars, downloads, contributors, registered agents) and time range
- Geographic: simple region bar chart or country list (no complex map needed for MVP). Can upgrade to map later.
- Category breakdown: horizontal stacked bar per protocol
- Protocol overlap: simple list of multi-protocol companies

### Section 3: Deployment Directory ("Who is using what?")

```
┌──────────────────────────────────────────────────────────────────┐
│ DEPLOYMENT DIRECTORY                                             │
│ [Search: company name...]                                        │
│ Filter: [All Protocols ▼] [All Countries ▼] [All Categories ▼]  │
│ Sort: [Most Recent ▼]                                            │
│                                                                  │
│ ┌────────────────────────────────────────────────────────────┐   │
│ │ Company      │ Protocol(s) │ Country │ Category    │ Date  │   │
│ ├──────────────┼─────────────┼─────────┼─────────────┼───────┤   │
│ │ PubMatic     │ AdCP MCP A2A│ US      │ Media Trad. │ Mar 26│   │
│ │ Amnet/Dentsu │ AdCP MCP    │ FR      │ Media Trad. │ Mar 26│   │
│ │ Optable      │ AdCP MCP    │ CA      │ Infra       │ Feb 26│   │
│ │ Magnite      │ AdCP        │ US      │ Media Trad. │ Jan 26│   │
│ │ Scope3       │ AdCP        │ US      │ Measurement │ Jan 26│   │
│ │ ...          │             │         │             │       │   │
│ └────────────────────────────────────────────────────────────┘   │
│                                                                  │
│ 87 known deployments across 14 countries                         │
│ Sources: AdCP Registry, IAB Agent Registry, GitHub, news         │
│ [Submit a deployment →] (link to form or email)                  │
└──────────────────────────────────────────────────────────────────┘
```

Searchable, filterable, sortable table. Each row links to the source URL. Pagination if > 50 entries.

## Data Collection Agent

### `/opt/pievra-analytics/collector.py`

Same architecture pattern as existing `news_agent.py`:
- Function-based agents, entry point: `run() -> int`
- SQLite with WAL mode
- Error handling: catch all, log, continue
- Uses `httpx` for HTTP requests
- GitHub API: use token for higher rate limits (5000 req/h vs 60)

### Collection steps (daily):

1. **GitHub metrics**: For each protocol's primary repo, fetch:
   - Stars, forks, open issues count (REST API `/repos/{owner}/{repo}`)
   - Contributors count (REST API `/repos/{owner}/{repo}/contributors?per_page=1&anon=true`, read `Link` header for total)
   - Commits in last 30 days (REST API `/repos/{owner}/{repo}/commits?since={30d_ago}&per_page=1`, read `Link` header)

2. **npm downloads**: For each npm package:
   - `https://api.npmjs.org/downloads/point/last-week/{package}` -> weekly download count

3. **PyPI downloads**: For each PyPI package:
   - `https://pypistats.org/api/packages/{package}/recent` -> last_week count

4. **Registry scraping**: Protocol-specific:
   - AdCP: scrape https://adcontextprotocol.org/registry/ for agent count
   - A2A: scrape A2A directory for agent count
   - IAB: scrape IAB registry for ARTF + Agentic Audiences entries

5. **Contributor locations** (weekly, not daily - heavy API usage):
   - For each protocol repo, fetch contributors list
   - For new contributors, fetch their profile location
   - Normalize location strings to country codes (simple mapping: "San Francisco" -> US, "London" -> GB, "Paris" -> FR)

6. **Store snapshot**: Insert one row per protocol in `protocol_metrics` for today's date.

### Real-time fetch (on page load, cached 1h):

Next.js server component checks `metrics_cache` table. If `cached_at` > 1h ago, fetch fresh:
- GitHub stars for all 5 repos (5 API calls)
- npm weekly downloads for primary packages (5 API calls)
- Store in cache, return fresh values

### Cron schedule:

```
# Daily collection at 04:00 UTC (before news agent at 06:00)
0 4 * * * flock -n /tmp/pievra-analytics.lock python3 /opt/pievra-analytics/collector.py >> /var/log/pievra-analytics.log 2>&1
```

## Admin Integration

Extend existing `/news/admin` with:

### Deployments Manager (`/news/admin/deployments`)
- Table of all deployments with edit/delete
- "Add Deployment" form: company, protocol(s), country, category, use case, source URL, date
- Bulk import from CSV

### Auto-tagging from news
- When the news agent classifies an article with a protocol tag, check if it mentions a company deployment
- Flag for admin review rather than auto-inserting (to avoid false positives)

## Seed Data

Initial deployment directory should be seeded with known deployments from:
- AdCP founding members (Yahoo, PubMatic, Optable, Scope3, Swivel, Triton Digital, Magnite, Kargo, LG Ad Solutions, Raptive, The Weather Company, Samba TV, Butler/Till, Classify, Newton Research, AccuWeather)
- MCP ecosystem (major integrations: OpenAI, Google, Block, Anthropic)
- A2A ecosystem (Google, Salesforce, SAP, etc.)
- ARTF early adopters
- France agentic campaign (PubMatic AgenticOS + Amnet + Claude)

## Design System

Inherits existing Pievra tokens. Protocol colors for charts:
- AdCP: #1d4ed8 (blue)
- MCP: #065f46 (green)
- Agentic Audiences: #92400e (amber)
- ARTF: #9d174d (pink)
- A2A: #5b21b6 (purple)

Chart library: Recharts (React-native, SSR-compatible, lightweight). If bundle size is a concern, use Chart.js with dynamic import.

## SEO

- URL: `https://pievra.com/news/analytics`
- Title: "Protocol Analytics - Pievra | Live Adoption Metrics for AdCP, MCP, A2A, ARTF"
- Description: "Track real-time adoption of agentic advertising protocols. GitHub stars, npm downloads, geographic deployment, company directory."
- Structured data: Dataset schema
- Open Graph with dynamic chart image (stretch goal)

## Mobile Layout

- Scorecards: horizontal scroll (like reports carousel)
- Charts: full width, simplified (fewer data points)
- Directory table: card layout instead of table on mobile
- Filters: horizontal scroll chips
