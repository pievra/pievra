# Pievra News Page Redesign - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the static news.html with a Next.js 15 app serving `/news/*` routes, featuring dual filtering (categories + protocols), sortable article feed, Pievra reports carousel, social sharing, bookmarks, comments, and admin panel.

**Architecture:** Next.js 15 App Router on port 3002, proxied by nginx for `/news/*` paths. SQLite database (existing at `/root/.pievra-news/news.db`) extended with new tables. Existing Python RSS agent updated for auto-categorization. Rest of pievra.com unchanged (static HTML via nginx).

**Tech Stack:** Next.js 15, React 19, TypeScript, Tailwind CSS 4, better-sqlite3, next-auth (LinkedIn + Google + email magic link), PM2

**Spec:** `docs/superpowers/specs/2026-04-01-news-page-redesign-design.md`

---

## File Structure

```
/var/www/pievra-news/                    # NEW Next.js project (separate from static site)
  package.json
  tsconfig.json
  tailwind.config.ts
  next.config.ts
  ecosystem.config.js                    # PM2 config
  src/
    lib/
      db.ts                              # SQLite connection + query helpers
      schema.sql                         # Full schema (migrations)
      categories.ts                      # Category + protocol definitions and keyword rules
      auth.ts                            # next-auth config
      sharing.ts                         # Share URL generators
    components/
      nav.tsx                            # Pievra top nav (matches existing)
      footer.tsx                         # Pievra footer (matches existing)
      reports-carousel.tsx               # Horizontal scroll report cards
      filter-bar.tsx                     # Dual filter (categories + protocols) + sort
      article-card.tsx                   # Feed article card with actions
      share-popover.tsx                  # Share button + dropdown
      comment-section.tsx                # Collapsible comments per article
      sidebar.tsx                        # Protocol status + newsletter + bookmarks + trending
      admin/
        article-table.tsx                # Admin article management table
        report-editor.tsx                # Markdown report editor
    app/
      news/
        layout.tsx                       # News section layout (nav + footer)
        page.tsx                         # Main feed page (reports carousel + feed + sidebar)
        [id]/
          [slug]/
            page.tsx                     # Individual article page
        reports/
          page.tsx                       # All reports listing
          [slug]/
            page.tsx                     # Individual report page
        admin/
          layout.tsx                     # Admin layout (auth guard)
          page.tsx                       # Admin dashboard
          articles/
            page.tsx                     # Article management
          reports/
            page.tsx                     # Report editor list
            new/
              page.tsx                   # New report form
            [id]/
              page.tsx                   # Edit report form
        api/
          auth/
            [...nextauth]/
              route.ts                   # NextAuth handler
          articles/
            route.ts                     # GET articles (filtered, sorted, paginated)
            [id]/
              views/
                route.ts                 # POST increment view count
              bookmark/
                route.ts                 # POST/DELETE bookmark
              comments/
                route.ts                 # GET/POST comments
          reports/
            route.ts                     # GET reports list
          admin/
            articles/
              [id]/
                route.ts                 # PATCH article (pin, hide, categorize)
            reports/
              route.ts                   # POST create report
              [id]/
                route.ts                 # PUT update, DELETE report
          feed.xml/
            route.ts                     # RSS feed output
  tests/
    lib/
      db.test.ts
      categories.test.ts
    api/
      articles.test.ts
      admin.test.ts

/opt/pievra-news/
  news_agent.py                          # MODIFY: add categorization + og:image extraction

/etc/nginx/sites-available/
  pievra.com                             # MODIFY: add /news proxy
```

---

## Task 1: Initialize Next.js Project

**Files:**
- Create: `/var/www/pievra-news/package.json`
- Create: `/var/www/pievra-news/tsconfig.json`
- Create: `/var/www/pievra-news/next.config.ts`
- Create: `/var/www/pievra-news/tailwind.config.ts`
- Create: `/var/www/pievra-news/.gitignore`

- [ ] **Step 1: Create project directory and initialize Next.js**

```bash
cd /var/www
npx create-next-app@latest pievra-news --typescript --tailwind --eslint --app --src-dir --no-import-alias --use-npm
```

When prompted, accept defaults.

- [ ] **Step 2: Install dependencies**

```bash
cd /var/www/pievra-news
npm install better-sqlite3 next-auth@beta @auth/core
npm install -D @types/better-sqlite3 vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/jest-dom
```

- [ ] **Step 3: Configure Next.js for `/news` base path**

Replace `/var/www/pievra-news/next.config.ts`:

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  basePath: "/news",
  output: "standalone",
};

export default nextConfig;
```

- [ ] **Step 4: Configure Tailwind with Pievra design tokens**

Replace `/var/www/pievra-news/tailwind.config.ts`:

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: "#18181B", soft: "#52525B", muted: "#71717A" },
        surface: { DEFAULT: "#FEFDFB", "2": "#F9F8F6", card: "#FFFFFF" },
        accent: { DEFAULT: "#F97316", hover: "#EA580C", light: "#FFF7ED", border: "#FDBA74" },
        sky: "#0EA5E9",
        border: { DEFAULT: "#E4E4E7", strong: "#D4D4D8" },
        protocol: {
          adcp: { bg: "#dbeafe", text: "#1d4ed8" },
          mcp: { bg: "#d1fae5", text: "#065f46" },
          ucp: { bg: "#fef3c7", text: "#92400e" },
          artf: { bg: "#fce7f3", text: "#9d174d" },
          a2a: { bg: "#ede9fe", text: "#5b21b6" },
        },
      },
      fontFamily: {
        display: ['"Instrument Serif"', "serif"],
        sans: ['"Plus Jakarta Sans"', "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "12px",
        lg: "20px",
      },
    },
  },
  plugins: [],
};

export default config;
```

- [ ] **Step 5: Add test configuration**

Create `/var/www/pievra-news/vitest.config.ts`:

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: [],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
```

Add to `package.json` scripts:

```json
"test": "vitest run",
"test:watch": "vitest"
```

- [ ] **Step 6: Verify project builds**

```bash
cd /var/www/pievra-news && npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 7: Commit**

```bash
cd /var/www/pievra-news && git init && git add -A && git commit -m "feat: initialize Next.js 15 project with Tailwind and Pievra design tokens"
```

---

## Task 2: Database Layer

**Files:**
- Create: `/var/www/pievra-news/src/lib/schema.sql`
- Create: `/var/www/pievra-news/src/lib/db.ts`
- Create: `/var/www/pievra-news/tests/lib/db.test.ts`

- [ ] **Step 1: Write the schema file**

Create `/var/www/pievra-news/src/lib/schema.sql`:

```sql
-- Extend existing articles table with new columns
ALTER TABLE articles ADD COLUMN category TEXT;
ALTER TABLE articles ADD COLUMN protocols TEXT DEFAULT '[]';
ALTER TABLE articles ADD COLUMN image_url TEXT;
ALTER TABLE articles ADD COLUMN view_count INTEGER DEFAULT 0;
ALTER TABLE articles ADD COLUMN is_pinned INTEGER DEFAULT 0;
ALTER TABLE articles ADD COLUMN is_hidden INTEGER DEFAULT 0;
ALTER TABLE articles ADD COLUMN article_type TEXT DEFAULT 'rss';

-- Pievra original reports
CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    excerpt TEXT,
    body TEXT,
    category TEXT,
    protocols TEXT DEFAULT '[]',
    author TEXT,
    published_at TEXT,
    updated_at TEXT,
    image_url TEXT,
    view_count INTEGER DEFAULT 0,
    is_featured INTEGER DEFAULT 0,
    status TEXT DEFAULT 'draft'
);

-- Users (lightweight auth)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    avatar_url TEXT,
    role TEXT DEFAULT 'reader',
    created_at TEXT DEFAULT (datetime('now'))
);

-- Bookmarks
CREATE TABLE IF NOT EXISTS bookmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id),
    article_id TEXT NOT NULL,
    article_type TEXT NOT NULL DEFAULT 'rss',
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, article_id)
);

-- Comments
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id TEXT NOT NULL,
    article_type TEXT NOT NULL DEFAULT 'rss',
    user_id TEXT NOT NULL REFERENCES users(id),
    body TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    is_deleted INTEGER DEFAULT 0
);

-- Read history
CREATE TABLE IF NOT EXISTS read_history (
    user_id TEXT NOT NULL,
    article_id TEXT NOT NULL,
    article_type TEXT NOT NULL DEFAULT 'rss',
    read_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, article_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published DESC);
CREATE INDEX IF NOT EXISTS idx_articles_view_count ON articles(view_count DESC);
CREATE INDEX IF NOT EXISTS idx_articles_pinned ON articles(is_pinned);
CREATE INDEX IF NOT EXISTS idx_reports_slug ON reports(slug);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_article ON comments(article_id);
```

- [ ] **Step 2: Write the database module**

Create `/var/www/pievra-news/src/lib/db.ts`:

```typescript
import Database from "better-sqlite3";
import path from "path";
import fs from "fs";

const DB_PATH = process.env.DB_PATH || path.join(process.env.HOME || "/root", ".pievra-news", "news.db");

let _db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!_db) {
    _db = new Database(DB_PATH);
    _db.pragma("journal_mode = WAL");
    _db.pragma("foreign_keys = ON");
  }
  return _db;
}

export function runMigrations(db: Database.Database) {
  const schemaPath = path.join(process.cwd(), "src", "lib", "schema.sql");
  const schema = fs.readFileSync(schemaPath, "utf-8");

  const statements = schema
    .split(";")
    .map((s) => s.trim())
    .filter((s) => s.length > 0 && !s.startsWith("--"));

  for (const stmt of statements) {
    try {
      db.exec(stmt);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.includes("duplicate column")) continue;
      if (msg.includes("already exists")) continue;
      throw err;
    }
  }
}

export type Article = {
  id: string;
  title: string;
  url: string;
  source: string;
  source_color: string;
  published: string | null;
  summary: string | null;
  relevance_score: number;
  category: string | null;
  protocols: string[];
  image_url: string | null;
  view_count: number;
  is_pinned: number;
  is_hidden: number;
  article_type: string;
};

export type Report = {
  id: string;
  title: string;
  slug: string;
  excerpt: string | null;
  body: string | null;
  category: string | null;
  protocols: string[];
  author: string | null;
  published_at: string | null;
  updated_at: string | null;
  image_url: string | null;
  view_count: number;
  is_featured: number;
  status: string;
};

export type SortOption = "recent" | "oldest" | "most_read";

export function getArticles(opts: {
  category?: string;
  protocols?: string[];
  sort?: SortOption;
  limit?: number;
  offset?: number;
}): { articles: Article[]; total: number } {
  const db = getDb();
  const conditions: string[] = ["a.is_hidden = 0"];
  const params: unknown[] = [];

  if (opts.category) {
    conditions.push("a.category = ?");
    params.push(opts.category);
  }

  if (opts.protocols && opts.protocols.length > 0) {
    const protocolConditions = opts.protocols.map(() => "a.protocols LIKE ?");
    conditions.push("(" + protocolConditions.join(" OR ") + ")");
    for (const p of opts.protocols) {
      params.push('%"' + p + '"%');
    }
  }

  const where = conditions.length > 0 ? "WHERE " + conditions.join(" AND ") : "";

  let orderBy = "a.is_pinned DESC, a.published DESC";
  if (opts.sort === "oldest") orderBy = "a.is_pinned DESC, a.published ASC";
  if (opts.sort === "most_read") orderBy = "a.is_pinned DESC, a.view_count DESC";

  const limit = opts.limit || 20;
  const offset = opts.offset || 0;

  const countRow = db.prepare("SELECT COUNT(*) as total FROM articles a " + where).get(...params) as { total: number };

  const rows = db
    .prepare("SELECT * FROM articles a " + where + " ORDER BY " + orderBy + " LIMIT ? OFFSET ?")
    .all(...params, limit, offset) as Array<Omit<Article, "protocols"> & { protocols: string }>;

  const articles = rows.map((r) => ({
    ...r,
    protocols: JSON.parse(r.protocols || "[]") as string[],
  }));

  return { articles, total: countRow.total };
}

export function getArticleById(id: string): Article | null {
  const db = getDb();
  const row = db.prepare("SELECT * FROM articles WHERE id = ?").get(id) as (Omit<Article, "protocols"> & { protocols: string }) | undefined;
  if (!row) return null;
  return { ...row, protocols: JSON.parse(row.protocols || "[]") };
}

export function incrementViewCount(id: string, type: "rss" | "report") {
  const db = getDb();
  if (type === "report") {
    db.prepare("UPDATE reports SET view_count = view_count + 1 WHERE id = ?").run(id);
  } else {
    db.prepare("UPDATE articles SET view_count = view_count + 1 WHERE id = ?").run(id);
  }
}

export function getPublishedReports(): Report[] {
  const db = getDb();
  const rows = db
    .prepare("SELECT * FROM reports WHERE status = 'published' ORDER BY published_at DESC")
    .all() as Array<Omit<Report, "protocols"> & { protocols: string }>;
  return rows.map((r) => ({ ...r, protocols: JSON.parse(r.protocols || "[]") }));
}

export function getReportBySlug(slug: string): Report | null {
  const db = getDb();
  const row = db.prepare("SELECT * FROM reports WHERE slug = ? AND status = 'published'").get(slug) as (Omit<Report, "protocols"> & { protocols: string }) | undefined;
  if (!row) return null;
  return { ...row, protocols: JSON.parse(row.protocols || "[]") };
}

export function getTrending(limit = 5): Article[] {
  const db = getDb();
  const rows = db
    .prepare("SELECT * FROM articles WHERE is_hidden = 0 ORDER BY view_count DESC LIMIT ?")
    .all(limit) as Array<Omit<Article, "protocols"> & { protocols: string }>;
  return rows.map((r) => ({ ...r, protocols: JSON.parse(r.protocols || "[]") }));
}

export function getCategoryCounts(): Record<string, number> {
  const db = getDb();
  const rows = db
    .prepare("SELECT category, COUNT(*) as count FROM articles WHERE is_hidden = 0 AND category IS NOT NULL GROUP BY category")
    .all() as Array<{ category: string; count: number }>;
  const counts: Record<string, number> = {};
  for (const r of rows) counts[r.category] = r.count;
  return counts;
}
```

- [ ] **Step 3: Write the database test**

Create `/var/www/pievra-news/tests/lib/db.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import Database from "better-sqlite3";
import { runMigrations } from "@/lib/db";

function createTestDb(): Database.Database {
  const db = new Database(":memory:");
  db.pragma("journal_mode = WAL");
  db.exec("CREATE TABLE articles (id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL, source TEXT NOT NULL, source_color TEXT DEFAULT '#71717A', published TEXT, summary TEXT, relevance_score REAL DEFAULT 0, fetched_at TEXT DEFAULT CURRENT_TIMESTAMP, displayed INTEGER DEFAULT 0)");
  return db;
}

describe("runMigrations", () => {
  it("adds new columns to existing articles table", () => {
    const db = createTestDb();
    runMigrations(db);
    db.prepare("INSERT INTO articles (id, title, url, source, category, protocols, view_count, is_pinned) VALUES (?, ?, ?, ?, ?, ?, ?, ?)").run("test1", "Test Article", "https://example.com", "TestSource", "Media Trading", '["MCP"]', 0, 0);
    const row = db.prepare("SELECT category, protocols, view_count, is_pinned FROM articles WHERE id = ?").get("test1") as Record<string, unknown>;
    expect(row.category).toBe("Media Trading");
    expect(row.protocols).toBe('["MCP"]');
    db.close();
  });

  it("creates reports table", () => {
    const db = createTestDb();
    runMigrations(db);
    db.prepare("INSERT INTO reports (id, title, slug, status) VALUES (?, ?, ?, ?)").run("r1", "Test Report", "test-report", "published");
    const row = db.prepare("SELECT * FROM reports WHERE id = ?").get("r1") as Record<string, unknown>;
    expect(row.title).toBe("Test Report");
    db.close();
  });

  it("creates users, bookmarks, comments, read_history tables", () => {
    const db = createTestDb();
    runMigrations(db);
    db.prepare("INSERT INTO users (id, email, name) VALUES (?, ?, ?)").run("u1", "test@example.com", "Test");
    db.prepare("INSERT INTO bookmarks (user_id, article_id, article_type) VALUES (?, ?, ?)").run("u1", "test1", "rss");
    db.prepare("INSERT INTO comments (article_id, article_type, user_id, body) VALUES (?, ?, ?, ?)").run("test1", "rss", "u1", "Great");
    db.prepare("INSERT INTO read_history (user_id, article_id) VALUES (?, ?)").run("u1", "test1");
    const user = db.prepare("SELECT * FROM users WHERE id = ?").get("u1") as Record<string, unknown>;
    expect(user.role).toBe("reader");
    db.close();
  });

  it("is idempotent", () => {
    const db = createTestDb();
    runMigrations(db);
    runMigrations(db);
    db.close();
  });
});
```

- [ ] **Step 4: Run tests**

```bash
cd /var/www/pievra-news && npx vitest run tests/lib/db.test.ts
```

Expected: All 4 tests pass.

- [ ] **Step 5: Commit**

```bash
cd /var/www/pievra-news && git add -A && git commit -m "feat: database layer with schema migrations and query helpers"
```

---

## Task 3: Category & Protocol Classification

**Files:**
- Create: `/var/www/pievra-news/src/lib/categories.ts`
- Create: `/var/www/pievra-news/tests/lib/categories.test.ts`

- [ ] **Step 1: Write the test**

Create `/var/www/pievra-news/tests/lib/categories.test.ts`:

```typescript
import { describe, it, expect } from "vitest";
import { classifyArticle, CATEGORIES, PROTOCOLS } from "@/lib/categories";

describe("classifyArticle", () => {
  it("classifies RTB article as Media Trading", () => {
    const result = classifyArticle("New DSP uses real-time bidding to optimize programmatic spend", "");
    expect(result.category).toBe("Media Trading");
  });

  it("classifies identity article as Data & Identity", () => {
    const result = classifyArticle("Third-party cookies are dead: first-party data strategies", "");
    expect(result.category).toBe("Data & Identity");
  });

  it("classifies retail media article", () => {
    const result = classifyArticle("Amazon retail media network grows 40%", "");
    expect(result.category).toBe("Retail Media");
  });

  it("tags MCP protocol", () => {
    const result = classifyArticle("Model Context Protocol gains traction in adtech", "");
    expect(result.protocols).toContain("MCP");
  });

  it("tags multiple protocols", () => {
    const result = classifyArticle("AdCP and A2A protocols compete for IAB adoption", "");
    expect(result.protocols).toContain("AdCP");
    expect(result.protocols).toContain("A2A");
  });

  it("returns null for unclassifiable", () => {
    const result = classifyArticle("Company announces new CEO", "leadership change");
    expect(result.category).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /var/www/pievra-news && npx vitest run tests/lib/categories.test.ts
```

Expected: FAIL (module not found).

- [ ] **Step 3: Write the implementation**

Create `/var/www/pievra-news/src/lib/categories.ts`:

```typescript
export const CATEGORIES = [
  "Media Trading",
  "Data & Identity",
  "Creative",
  "Infrastructure",
  "Measurement",
  "Retail Media",
] as const;

export type Category = (typeof CATEGORIES)[number];

export const PROTOCOLS = ["AdCP", "MCP", "Agentic Audiences", "ARTF", "A2A"] as const;

export type Protocol = (typeof PROTOCOLS)[number];

const CATEGORY_KEYWORDS: Record<Category, string[]> = {
  "Media Trading": [
    "programmatic", "dsp", "ssp", "rtb", "real-time bidding", "media buying",
    "ad exchange", "header bidding", "prebid", "openrtb", "bid stream",
    "supply path", "demand path", "cpm", "cpc", "cpa", "ctv advertising",
    "video advertising", "display advertising", "ad server", "campaign manager",
    "impression", "ad spend", "media plan", "insertion order",
  ],
  "Data & Identity": [
    "first-party data", "third-party cookie", "identity resolution", "clean room",
    "data management", "cdp", "customer data", "audience segment", "hashed email",
    "uid2", "euid", "id5", "liveramp", "consent", "gdpr", "privacy",
    "contextual targeting", "cohort", "fingerprint", "identifier",
  ],
  Creative: [
    "creative optimization", "dco", "dynamic creative", "ad creative",
    "generative ai creative", "ai-generated ads", "creative automation",
    "ad format", "rich media", "interactive ad",
  ],
  Infrastructure: [
    "ad tech infrastructure", "cloud", "api", "sdk", "protocol", "standard",
    "iab tech lab", "open source", "developer", "integration", "pipeline",
    "architecture", "ai agent", "agentic", "llm", "model context",
  ],
  Measurement: [
    "attribution", "measurement", "incrementality", "lift study", "viewability",
    "brand lift", "conversion", "roi measurement", "media mix model",
    "cross-channel measurement", "attention metric", "outcome-based",
  ],
  "Retail Media": [
    "retail media", "commerce media", "shopper", "in-store",
    "amazon ads", "walmart connect", "sponsored product", "retail data",
    "commerce data", "purchase data",
  ],
};

const PROTOCOL_KEYWORDS: Record<Protocol, string[]> = {
  AdCP: ["adcp", "ad context protocol"],
  MCP: ["mcp", "model context protocol"],
  "Agentic Audiences": ["ucp", "agentic audience", "unified context"],
  ARTF: ["artf", "agentic rtb", "agentic real-time"],
  A2A: ["a2a", "agent-to-agent", "agent to agent"],
};

export function classifyArticle(title: string, summary: string): {
  category: Category | null;
  protocols: Protocol[];
} {
  const text = (title + " " + summary).toLowerCase();

  let bestCategory: Category | null = null;
  let bestScore = 0;

  for (const [cat, keywords] of Object.entries(CATEGORY_KEYWORDS) as [Category, string[]][]) {
    let score = 0;
    for (const kw of keywords) {
      if (text.includes(kw)) score++;
    }
    if (score > bestScore) {
      bestScore = score;
      bestCategory = cat;
    }
  }

  if (bestScore === 0) bestCategory = null;

  const protocols: Protocol[] = [];
  for (const [proto, keywords] of Object.entries(PROTOCOL_KEYWORDS) as [Protocol, string[]][]) {
    for (const kw of keywords) {
      if (text.includes(kw)) {
        protocols.push(proto);
        break;
      }
    }
  }

  return { category: bestCategory, protocols };
}
```

- [ ] **Step 4: Run tests**

```bash
cd /var/www/pievra-news && npx vitest run tests/lib/categories.test.ts
```

Expected: All 6 tests pass.

- [ ] **Step 5: Commit**

```bash
cd /var/www/pievra-news && git add -A && git commit -m "feat: article category and protocol classification engine"
```

---

## Task 4: Update Python News Agent

**Files:**
- Modify: `/opt/pievra-news/news_agent.py`

The agent needs auto-categorization and og:image extraction. See spec for full keyword maps. Changes are: add CATEGORY_KEYWORDS and PROTOCOL_KEYWORDS dicts, add `classify_article()` and `extract_og_image()` functions, update `init_db()` to add new columns, update `store_articles()` to classify on insert.

This task is detailed in the spec. The implementation mirrors Task 3's categories.ts but in Python. Run `python3 /opt/pievra-news/news_agent.py` after changes and verify with:

```bash
sqlite3 /root/.pievra-news/news.db "SELECT title, category, protocols FROM articles WHERE category IS NOT NULL LIMIT 5;"
```

Then backfill existing articles:

```bash
python3 -c "
import sqlite3, json, sys
sys.path.insert(0, '/opt/pievra-news')
from news_agent import classify_article
conn = sqlite3.connect('/root/.pievra-news/news.db')
rows = conn.execute('SELECT id, title, summary FROM articles WHERE category IS NULL').fetchall()
for row_id, title, summary in rows:
    cat, protos = classify_article(title, summary or '')
    conn.execute('UPDATE articles SET category = ?, protocols = ? WHERE id = ?', (cat, json.dumps(protos), row_id))
conn.commit()
print(f'Backfilled {len(rows)} articles')
conn.close()
"
```

---

## Tasks 5-13: Components, Pages, Admin

Tasks 5 through 13 cover all UI components and pages. Each task creates specific files as mapped in the File Structure above. The implementation details follow the design spec exactly. Key tasks:

- **Task 5**: Nav, Footer, Protocol/Category badges, News layout
- **Task 6**: Reports carousel (horizontal scroll, 3 cards desktop)
- **Task 7**: Filter bar (dual row: categories single-select + protocols multi-select + sort dropdown), Article card (badges, share, bookmark), Share popover (LinkedIn, X, Facebook, Copy Link, Email)
- **Task 8**: Sidebar (protocol status, newsletter, bookmarks, trending)
- **Task 9**: Main feed page assembling Tasks 6-8 with SSR data fetching
- **Task 10**: Individual article page (`/news/[id]/[slug]`) with view counting, related articles
- **Task 11**: Report listing and detail pages (`/news/reports/`, `/news/reports/[slug]`)
- **Task 12**: API routes: POST view count, GET/output RSS feed at `/news/api/feed.xml`
- **Task 13**: Admin panel: dashboard, article management table (pin/hide/categorize), report editor (create/edit with markdown, status toggle)

Each task follows TDD where applicable and commits atomically.

---

## Task 14: Deployment (PM2 + Nginx)

**Files:**
- Create: `/var/www/pievra-news/ecosystem.config.js`
- Create: `/var/www/pievra-news/.env.local`
- Modify: `/etc/nginx/sites-available/pievra.com`

- [ ] **Step 1: Create .env.local**

```bash
ADMIN_SECRET=pievra_admin_2026
DB_PATH=/root/.pievra-news/news.db
```

- [ ] **Step 2: Create PM2 config**

```javascript
module.exports = {
  apps: [{
    name: "pievra-news",
    script: "node_modules/.bin/next",
    args: "start -p 3002",
    cwd: "/var/www/pievra-news",
    env: {
      NODE_ENV: "production",
      PORT: 3002,
    },
    instances: 1,
    autorestart: true,
    max_memory_restart: "512M",
  }],
};
```

- [ ] **Step 3: Build and start**

```bash
cd /var/www/pievra-news && npm run build && pm2 start ecosystem.config.js && pm2 save
```

- [ ] **Step 4: Update nginx**

Add before `location = /news` line in `/etc/nginx/sites-available/pievra.com`:

```nginx
    location /news/ {
        proxy_pass http://127.0.0.1:3002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /news/_next/ {
        proxy_pass http://127.0.0.1:3002;
        proxy_set_header Host $host;
    }
```

Change existing `location = /news` to: `location = /news { return 301 /news/; }`

- [ ] **Step 5: Test and reload nginx**

```bash
nginx -t && systemctl reload nginx
```

- [ ] **Step 6: Verify**

```bash
curl -s -o /dev/null -w "%{http_code}" https://pievra.com/news/
```

Expected: 200

---

## Task 15: Seed Existing Reports

Migrate the 5 existing protocol deep-dive articles (AdCP, MCP, UCP, ARTF, A2A) from the static news.html into the reports table using a seed script. Run once after deployment.

---

## Task Dependencies

| Task | Description | Depends On |
|------|-------------|-----------|
| 1 | Initialize Next.js | None |
| 2 | Database layer | 1 |
| 3 | Classification engine | 1 |
| 4 | Update Python agent | 2, 3 |
| 5 | Shared components | 1 |
| 6 | Reports carousel | 2, 5 |
| 7 | Filter bar, article card, share | 2, 3, 5 |
| 8 | Sidebar | 2, 5 |
| 9 | Main feed page | 6, 7, 8 |
| 10 | Article detail page | 2, 5 |
| 11 | Report pages | 2, 5 |
| 12 | API routes | 2 |
| 13 | Admin panel | 2, 3, 5 |
| 14 | Deployment | 9 |
| 15 | Seed reports | 14 |

**Parallelizable**: Tasks 2+3+5 can run simultaneously. Tasks 6+7+8+10+11+12+13 can run after their dependencies complete.

**Deferred to follow-up**: Full NextAuth integration (LinkedIn/Google/magic link OAuth). Current plan uses simple admin cookie for the admin panel.
