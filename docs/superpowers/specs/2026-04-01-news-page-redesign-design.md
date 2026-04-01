# Pievra News Page Redesign - Design Spec

**Date**: 2026-04-01
**Status**: Approved

## Overview

Transform the Pievra news page from a static 103KB HTML file with hardcoded protocol articles and RSS feed injection into a dynamic, framework-backed news platform with dual filtering (industry categories + protocol tags), sortable feeds, social sharing, user bookmarks, comments, and an admin panel.

## Goals

1. Replace the oversized community discussion section with a functional, collapsible comment system
2. Add industry-topic category filtering alongside existing protocol tags
3. Feature Pievra's original reports prominently above the RSS feed
4. Enable article triage: sort by date, freshness, popularity
5. Add social sharing (LinkedIn, X, Facebook, email)
6. Add user bookmarks and read-tracking
7. Admin tools for pinning, hiding, categorizing articles and publishing reports

## Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | Next.js 15 (App Router) | SSR for SEO. API routes for dynamic features. PM2 already on VPS. |
| Database | SQLite (extend existing `/root/.pievra-news/news.db`) | Every VPS project uses SQLite. News agent already writes here. |
| Styling | Tailwind CSS | Matches existing design tokens. Fast iteration. |
| Auth | OAuth (LinkedIn + Google) + magic link email | B2B audience fits LinkedIn. Google as fallback. Magic link for minimal friction. |
| Deployment | PM2 on VPS, nginx reverse proxy | No new infrastructure. |

## Architecture

```
nginx (port 80/443)
  |-- /news/*  -->  proxy_pass to Next.js (PM2, port 3002)
  |-- /*       -->  static files from /var/www/pievra/
```

Next.js handles ONLY `/news/*` routes. The rest of pievra.com stays as static HTML.

The existing Python news agent (`/opt/pievra-news/news_agent.py`) continues fetching RSS feeds on its cron schedule and writing to SQLite. Next.js reads from the same database. The agent gets two additions: auto-categorization via keyword rules, and og:image extraction.

## Data Model

### articles (EXISTING - extended)

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PK | Hash (existing) |
| title | TEXT | |
| url | TEXT | |
| source | TEXT | |
| source_color | TEXT | |
| published | TEXT | |
| summary | TEXT | |
| relevance_score | REAL | |
| fetched_at | TEXT | |
| displayed | INTEGER | |
| category | TEXT | NEW. Media Trading, Data & Identity, Creative, Infrastructure, Measurement, Retail Media |
| protocols | TEXT | NEW. JSON array: ["AdCP", "MCP"] |
| image_url | TEXT | NEW. og:image extracted by agent |
| view_count | INTEGER DEFAULT 0 | NEW |
| is_pinned | INTEGER DEFAULT 0 | NEW |
| is_hidden | INTEGER DEFAULT 0 | NEW |
| article_type | TEXT | NEW. 'rss' or 'report' |

### reports (NEW)

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PK | |
| title | TEXT | |
| slug | TEXT UNIQUE | URL-safe |
| excerpt | TEXT | |
| body | TEXT | Markdown |
| category | TEXT | |
| protocols | TEXT | JSON array |
| author | TEXT | |
| published_at | TEXT | |
| updated_at | TEXT | |
| image_url | TEXT | |
| view_count | INTEGER DEFAULT 0 | |
| is_featured | INTEGER DEFAULT 0 | |
| status | TEXT | draft, published |

### users (NEW)

| Column | Type | Notes |
|--------|------|-------|
| id | TEXT PK | |
| email | TEXT UNIQUE | |
| name | TEXT | |
| avatar_url | TEXT | |
| role | TEXT DEFAULT 'reader' | reader, admin |
| created_at | TEXT | |

### bookmarks (NEW)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| user_id | TEXT | FK users.id |
| article_id | TEXT | |
| article_type | TEXT | 'rss' or 'report' |
| created_at | TEXT | |

### comments (NEW)

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK AUTOINCREMENT | |
| article_id | TEXT | |
| article_type | TEXT | |
| user_id | TEXT | FK users.id |
| body | TEXT | |
| created_at | TEXT | |
| is_deleted | INTEGER DEFAULT 0 | |

### read_history (NEW)

| Column | Type | Notes |
|--------|------|-------|
| user_id | TEXT | Composite PK |
| article_id | TEXT | Composite PK |
| article_type | TEXT | |
| read_at | TEXT | |

## Page Layout

### Hybrid: Reports Carousel + Sortable Feed

The page has two distinct sections:

### Section 1: Pievra Reports Carousel

- Full-width horizontal scroll of report cards
- 3 visible on desktop, 1 + peek on mobile
- Each card: image/gradient background, protocol badges, title, excerpt, date, read time
- "View All" link to `/news/reports`
- Cards link to `/news/reports/[slug]` (individual report page)

### Section 2: Industry Feed

Two-column layout: main feed + sidebar.

#### Filter & Sort Bar (sticky below nav when scrolling past reports)

- **Row 1 - Categories** (single-select): All, Media Trading, Data & Identity, Creative, Infrastructure, Measurement, Retail Media. Each button shows a live count of matching articles in parentheses.
- **Row 2 - Protocols** (multi-select): AdCP, MCP, Agentic Audiences/UCP, ARTF, A2A
- **Row 3 - Sort**: dropdown (Most Recent, Oldest, Most Read) + live article count

#### Article Cards (main column)

Each card contains:
- Category badge + protocol badge(s) + relative timestamp
- Article title (links to `/news/[id]/[slug]`)
- Source name
- Two-line excerpt
- Action row: view count, comment count, bookmark button, share button
- Collapsed comments: "X comments" link expands inline
- Pinned articles (admin-set) display first with pin indicator
- Read articles get subtle visual dimming for logged-in users

#### Share Popover

Triggered by share icon on each card:
- Copy Link (copies `/news/[id]/[slug]` URL)
- LinkedIn (share intent)
- X / Twitter (share intent)
- Facebook (share intent)
- Email (mailto with pre-filled subject/body)
- Mobile: uses `navigator.share()` when available

#### Sidebar (sticky)

- Protocol Status card (6 protocols with version + status badge)
- Newsletter signup (email input + subscribe button)
- Your Bookmarks (logged-in only, list of saved articles, "View all" link)
- Trending (top 3 most-read articles)

### Individual Article Page (`/news/[id]/[slug]`)

- Full article content (RSS: excerpt + link to source; reports: full markdown body)
- Prominent share buttons at top
- Full comments section (not collapsed)
- Related articles (same category or protocol)
- Back to feed link
- Proper Open Graph + Twitter Card meta tags

### Individual Report Page (`/news/reports/[slug]`)

- Full report body (rendered markdown)
- Author, date, read time
- Protocol badges
- Share buttons
- Comments section
- Related reports

## Authentication

- **LinkedIn OAuth** (primary, fits B2B audience)
- **Google OAuth** (secondary)
- **Magic link email** (fallback)
- Session via HTTP-only cookie
- Minimal user data: id, email, name, avatar, role
- Admin role assigned manually in DB

## Admin Panel (`/news/admin`)

Protected by admin role check.

### Article Management
- Table view of all articles (RSS + reports)
- Quick actions per row: Pin/Unpin, Hide/Show, Edit Category, Edit Protocol Tags
- Bulk actions: re-categorize, hide multiple
- Search/filter within admin

### Report Editor
- Create/edit with markdown editor
- Fields: title, slug, excerpt, body, category, protocols, featured image, status
- Preview before publishing

### Category Rules
- View/edit keyword-to-category mapping used by Python agent
- Manual override for any auto-assignment

### Dashboard
- Total articles, views today, top 5 most read, new comments pending

## Python Agent Updates

Two additions to `/opt/pievra-news/news_agent.py`:

1. **Auto-categorize**: keyword rules map articles to categories and protocol tags when fetched
2. **Image extraction**: fetch og:image from article URLs for card thumbnails

Agent continues running on existing cron schedule, writing to same SQLite DB.

## Mobile Layout

- Reports carousel: single card visible with peek of next, swipeable
- Filter bars: horizontal scroll chips
- Article cards: full-width, stacked
- Sidebar: collapses below feed
- Share: native `navigator.share()` on mobile, popover fallback

## SEO

- Each article/report gets its own URL with meta tags, Open Graph, Twitter Cards
- Report pages get Article structured data (JSON-LD)
- Feed page has canonical URL
- RSS feed output at `/news/feed.xml`

## Design System

Inherits existing Pievra tokens:
- Fonts: Instrument Serif (display), Plus Jakarta Sans (body)
- Colors: --ink (#18181B), --accent (#F97316), --surface (#FEFDFB), --sky (#0EA5E9)
- Border radius: 12px default, 20px large
- Protocol badge colors: AdCP=blue, MCP=green, UCP=yellow, ARTF=pink, A2A=purple
- Category badges: neutral style (gray border, dark text) to visually distinguish from protocol badges
