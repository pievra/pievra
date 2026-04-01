# Pievra MCP Server - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an MCP server exposing 7 tools for agentic advertising intelligence (agent discovery, protocol metrics, deployments, compatibility, stack recommendations, news), deployable as both a hosted SSE service and an npm package with stdio transport.

**Architecture:** Single TypeScript project using `@modelcontextprotocol/sdk`. Data provider abstraction: hosted mode reads SQLite directly, local mode reads a JSON snapshot. Tools are pure functions that take a data provider and return structured results with `data_as_of` timestamps.

**Tech Stack:** TypeScript, @modelcontextprotocol/sdk, better-sqlite3, vitest, PM2

**Spec:** `docs/superpowers/specs/2026-04-01-pievra-mcp-server-design.md`

---

## File Structure

```
/var/www/pievra-mcp/
  package.json
  tsconfig.json
  vitest.config.ts
  ecosystem.config.js
  src/
    index.ts                        # Entry: --stdio or --sse, starts server
    server.ts                       # MCP server: registers all 7 tools
    data/
      types.ts                      # Agent, Deployment, Metrics, Article types + DataProvider interface
      compatibility-matrix.ts       # Hardcoded protocol relationship map
      hosted-provider.ts            # Reads from SQLite (news.db + analytics.db)
      local-provider.ts             # Reads from JSON snapshot
      snapshot.json                 # Bundled data for npm package
    tools/
      discover-agents.ts            # Tool 1
      check-protocol-support.ts     # Tool 2
      get-protocol-metrics.ts       # Tool 3
      find-deployments.ts           # Tool 4
      get-compatibility.ts          # Tool 5
      recommend-stack.ts            # Tool 6
      get-market-news.ts            # Tool 7
    api/
      snapshot-handler.ts           # HTTP handler for GET /mcp/api/snapshot
  scripts/
    migrate-agents.ts               # Extract AGENTS from marketplace.html to analytics.db
    generate-snapshot.ts            # Generate snapshot.json from SQLite
  tests/
    tools.test.ts
    compatibility.test.ts
```

---

## Task 1: Project Scaffold + Types + Data Provider Interface

**Files:**
- Create: `/var/www/pievra-mcp/package.json`
- Create: `/var/www/pievra-mcp/tsconfig.json`
- Create: `/var/www/pievra-mcp/vitest.config.ts`
- Create: `/var/www/pievra-mcp/src/data/types.ts`

Initialize project, install deps, define the core types and DataProvider interface that all tools depend on.

Dependencies: `@modelcontextprotocol/sdk`, `better-sqlite3`, `@types/better-sqlite3`
Dev: `typescript`, `vitest`, `tsx`

`types.ts` exports:
- `Agent` type: name, icon, category, version, status, featured, protocols (string[]), steward, description, tags (string[]), link
- `Deployment` type: company, protocol, country, region, category, use_case, announced_date
- `ProtocolMetrics` type: protocol, github_stars, npm_weekly_downloads, pypi_weekly_downloads, github_contributors, github_commits_30d, maturity, date
- `Article` type: title, source, url, category, protocols (string[]), published
- `CompatibilityResult` type: protocol_a, protocol_b, compatible, relationship, bridge_mechanism, notes
- `DataProvider` interface:
  ```typescript
  interface DataProvider {
    getAgents(opts?: { protocol?: string; category?: string; status?: string; query?: string }): Agent[];
    getDeployments(opts?: { protocol?: string; country?: string; category?: string; search?: string; limit?: number }): { deployments: Deployment[]; total: number };
    getMetrics(protocol?: string): ProtocolMetrics[];
    getArticles(opts?: { protocol?: string; category?: string; days?: number; limit?: number }): Article[];
    getDataTimestamp(): string;
  }
  ```

---

## Task 2: Compatibility Matrix

**Files:**
- Create: `/var/www/pievra-mcp/src/data/compatibility-matrix.ts`
- Create: `/var/www/pievra-mcp/tests/compatibility.test.ts`

Hardcoded map of all 10 protocol pairs with relationship type, bridge mechanism, and notes. Export function `getCompatibility(a: string, b: string): CompatibilityResult`.

The 10 pairs (order-independent lookup):
- AdCP+MCP: native
- AdCP+A2A: native
- ARTF+MCP: compatible
- ARTF+A2A: compatible
- Agentic Audiences+MCP: compatible
- AdCP+ARTF: complementary
- AdCP+Agentic Audiences: complementary
- ARTF+Agentic Audiences: compatible
- A2A+Agentic Audiences: no_direct_bridge
- MCP+A2A: complementary

Tests: lookup both directions (AdCP+MCP and MCP+AdCP return same result), unknown protocol returns error-like result.

---

## Task 3: Hosted Data Provider (SQLite)

**Files:**
- Create: `/var/www/pievra-mcp/src/data/hosted-provider.ts`

Implements `DataProvider` interface by reading from:
- `/root/.pievra-analytics/analytics.db` (agents, deployments, protocol_metrics tables)
- `/root/.pievra-news/news.db` (articles table)

Uses `better-sqlite3`. Each method runs a SQL query with optional filters. `getDataTimestamp()` returns the max date from protocol_metrics.

For `getAgents`: query the `agents` table (created in Task 5). Parse protocols and tags JSON fields.
For `getDeployments`: query deployments table with optional WHERE clauses.
For `getMetrics`: query latest protocol_metrics per protocol. Calculate momentum_30d_pct by comparing latest vs 30-days-ago snapshot.
For `getArticles`: query articles table with date filter (`published >= date('now', '-N days')`), protocol LIKE filter, category filter.

---

## Task 4: Local Data Provider (JSON Snapshot)

**Files:**
- Create: `/var/www/pievra-mcp/src/data/local-provider.ts`

Implements `DataProvider` by reading from an in-memory JSON object (loaded from `snapshot.json` or fetched from API).

Constructor: `new LocalProvider(data: SnapshotData)` where SnapshotData matches the snapshot shape.

Each method filters the in-memory arrays. Same interface as hosted provider.

Static factory: `LocalProvider.load()` - tries fetch from `https://pievra.com/mcp/api/snapshot` with 3s timeout, falls back to bundled `snapshot.json`.

---

## Task 5: Migrate Agents to SQLite

**Files:**
- Create: `/var/www/pievra-mcp/scripts/migrate-agents.ts`

One-time script that:
1. Reads `/var/www/pievra/marketplace.html`
2. Extracts the `var AGENTS = [...]` JS array via regex
3. Parses each agent object (handle JS-style unquoted keys)
4. Creates `agents` table in `/root/.pievra-analytics/analytics.db` if not exists
5. Inserts all agents with INSERT OR REPLACE
6. Logs count

Run with `npx tsx scripts/migrate-agents.ts`.

---

## Task 6: Seven Tool Implementations

**Files:**
- Create: `/var/www/pievra-mcp/src/tools/discover-agents.ts`
- Create: `/var/www/pievra-mcp/src/tools/check-protocol-support.ts`
- Create: `/var/www/pievra-mcp/src/tools/get-protocol-metrics.ts`
- Create: `/var/www/pievra-mcp/src/tools/find-deployments.ts`
- Create: `/var/www/pievra-mcp/src/tools/get-compatibility.ts`
- Create: `/var/www/pievra-mcp/src/tools/recommend-stack.ts`
- Create: `/var/www/pievra-mcp/src/tools/get-market-news.ts`
- Create: `/var/www/pievra-mcp/tests/tools.test.ts`

Each tool is a pure function: `(provider: DataProvider, input: ToolInput) => ToolOutput`.

Every output includes `data_as_of: provider.getDataTimestamp()`.

**discover_agents**: calls `provider.getAgents(opts)`, returns formatted list + count.

**check_protocol_support**: calls `provider.getDeployments({ search: input.company })`, groups by protocol, deduplicates, returns protocols array with use_case and announced_date.

**get_protocol_metrics**: calls `provider.getMetrics(input.protocol)`, adds maturity from a hardcoded map (MCP=Stable, AdCP=Beta, A2A=Stable, ARTF=Final, Agentic Audiences=Draft).

**find_deployments**: calls `provider.getDeployments(opts)`, returns list + total.

**get_compatibility**: calls `getCompatibility(a, b)` from compatibility-matrix.ts.

**recommend_stack**: combines getDeployments (filtered by market), getAgents (filtered by category), getMetrics (for ranking). Rule-based: find dominant protocol in market, match agents, assemble recommendation string.

**get_market_news**: calls `provider.getArticles(opts)`, returns list + count.

Tests: use a mock DataProvider with canned data. Test each tool's filtering, output shape, and edge cases (empty results, unknown protocol).

---

## Task 7: MCP Server Setup + Tool Registration

**Files:**
- Create: `/var/www/pievra-mcp/src/server.ts`

Creates MCP server using `@modelcontextprotocol/sdk`. Registers all 7 tools with:
- Name, description, input JSON schema (for MCP tool discovery)
- Handler function that calls the tool implementation with the data provider

The server constructor takes a `DataProvider` instance (injected by index.ts based on mode).

Tool schemas defined inline using the MCP SDK's `zodToJsonSchema` or plain JSON schema objects matching the spec's input types.

---

## Task 8: Entry Point (stdio + SSE)

**Files:**
- Create: `/var/www/pievra-mcp/src/index.ts`

Parses CLI args:
- `--stdio` (default): starts stdio transport, creates LocalProvider
- `--sse --port 3004`: starts SSE transport on given port, creates HostedProvider
- `--sse` without port: defaults to 3004

For SSE mode, also mounts the snapshot API handler at `/api/snapshot`.

`package.json` bin field: `"pievra-mcp": "./dist/index.js"` so `npx @pievra/mcp-server` works.

---

## Task 9: Snapshot Generator + API Handler

**Files:**
- Create: `/var/www/pievra-mcp/scripts/generate-snapshot.ts`
- Create: `/var/www/pievra-mcp/src/api/snapshot-handler.ts`

**generate-snapshot.ts**: reads from both SQLite databases, assembles SnapshotData object (agents, metrics, deployments, articles, compatibility matrix, generated_at), writes to `src/data/snapshot.json`. Run by cron every 6h and before npm publish.

**snapshot-handler.ts**: HTTP request handler for `GET /api/snapshot`. Reads cached snapshot from disk (regenerated every 6h), returns as JSON with appropriate headers.

---

## Task 10: Build, Deploy, Verify

**Files:**
- Create: `/var/www/pievra-mcp/ecosystem.config.js`
- Modify: `/etc/nginx/sites-enabled/pievra.com` (add /mcp proxy)

Steps:
1. Run migrate-agents script to populate agents table
2. Run generate-snapshot to create initial snapshot.json
3. Build TypeScript: `npm run build`
4. Start with PM2 on port 3004
5. Add nginx proxy: `location ^~ /mcp { proxy_pass http://127.0.0.1:3004; }`
6. Reload nginx
7. Verify SSE: `curl https://pievra.com/mcp` returns MCP handshake
8. Verify stdio: `echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | node dist/index.js --stdio`
9. Test a tool via MCP client
10. Add snapshot cron (every 6h)

---

## Task Dependencies

| Task | Description | Depends On |
|------|-------------|-----------|
| 1 | Scaffold + types + interface | None |
| 2 | Compatibility matrix | 1 |
| 3 | Hosted data provider (SQLite) | 1 |
| 4 | Local data provider (JSON) | 1 |
| 5 | Migrate agents to SQLite | 1 |
| 6 | 7 tool implementations + tests | 1, 2 |
| 7 | MCP server setup | 1, 6 |
| 8 | Entry point (stdio + SSE) | 7, 3, 4 |
| 9 | Snapshot generator + API | 3 |
| 10 | Deploy + verify | 5, 8, 9 |

**Parallelizable**: Tasks 2, 3, 4, 5 can all run after Task 1. Task 6 needs 1+2. Tasks 7-8 are sequential. Task 10 is final.
