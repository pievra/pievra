# Pievra MCP Server - Design Spec

**Date**: 2026-04-01
**Status**: Approved

## Overview

An MCP-compliant server exposing 7 tools for agentic advertising intelligence. Provides protocol discovery, adoption metrics, deployment directory, compatibility checking, stack recommendations, and market news. Positioned as the "Bloomberg Terminal" for agentic advertising: the intelligence layer that other agents consult before making decisions.

Primary consumer: production AI agents (buyer/seller agents, orchestrators) that call Pievra tools mid-workflow. Secondary: developers building agentic advertising systems.

## Architecture

Two deployment modes, same tool logic:

### Hosted Mode (Production)
- Runs on VPS at `/var/www/pievra-mcp/` as PM2 process (port 3004)
- nginx proxies `/mcp` to the server
- SSE transport for remote agent connections via `https://pievra.com/mcp`
- Reads directly from SQLite databases on disk
- Also serves a snapshot API at `GET /mcp/api/snapshot`

### Local Mode (npm package)
- Published as `@pievra/mcp-server`
- `npx @pievra/mcp-server` runs stdio transport
- Ships with bundled `data-snapshot.json`
- On startup: fetches fresh snapshot from `https://pievra.com/mcp/api/snapshot` if network available, falls back to bundled

### Data Flow
```
Hosted:
  Agent --SSE--> pievra.com/mcp --> MCP Server --> SQLite (news.db + analytics.db)

Local:
  Agent --stdio--> npx @pievra/mcp-server --> bundled JSON snapshot
                                          --> (optional) pievra.com/mcp/api/snapshot
```

## Tech Stack

- TypeScript
- `@modelcontextprotocol/sdk` (official MCP SDK, stdio + SSE transports)
- `better-sqlite3` (hosted mode, reading existing databases)
- PM2 (hosted deployment)
- npm (package distribution)

## Data Sources

### Hosted Mode
- `/root/.pievra-news/news.db` - articles table (for `get_market_news`)
- `/root/.pievra-analytics/analytics.db` - protocol_metrics, deployments tables (for metrics/deployment tools)
- `/root/.pievra-analytics/analytics.db` - agents table (NEW, migrated from marketplace.html AGENTS array)

### Agents Table Migration
The marketplace AGENTS array (26 agents, currently in a JS variable inside marketplace.html) must be moved to SQLite. New `agents` table in analytics.db:

| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| name | TEXT NOT NULL | |
| icon | TEXT | emoji |
| category | TEXT | infra, media, data, creative, measure |
| version | TEXT | e.g. "v2.0" |
| status | TEXT | live, beta |
| featured | INTEGER DEFAULT 0 | |
| protocols | TEXT | JSON array: ["AdCP", "MCP"] |
| steward | TEXT | e.g. "Prebid.org" |
| description | TEXT | |
| tags | TEXT | JSON array |
| link | TEXT | GitHub or docs URL |

One-time migration script extracts from marketplace.html and inserts into this table.

### Local Mode
- `data-snapshot.json` bundled in npm package, containing:
  - agents: full list
  - metrics: latest snapshot per protocol
  - deployments: full list
  - articles: last 50 articles
  - compatibility: full matrix
  - generated_at: ISO timestamp

### Snapshot API
`GET /mcp/api/snapshot` served by the MCP server process in hosted mode.
- Returns the full JSON snapshot
- Regenerated and cached every 6 hours
- Used by local npm clients on startup

## Freshness Model

Every tool response includes a `data_as_of` field (ISO timestamp) indicating when the underlying data was last collected. No live fetching from external APIs. Calling agents can inspect `data_as_of` to decide whether to trust the data.

- Metrics: refreshed daily at 04:00 UTC by the collector
- Deployments: updated manually via admin panel or auto-tagged from news
- Agents: updated when marketplace changes
- Articles: refreshed daily at 06:00 UTC by the news agent

## Tools

### 1. discover_agents
Find agents in the Pievra marketplace.

**Input:**
```typescript
{
  protocol?: string,    // "AdCP", "MCP", "A2A", "ARTF", "Agentic Audiences"
  category?: string,    // "infra", "media", "data", "creative", "measure"
  status?: "live" | "beta",
  query?: string        // free-text search across name, description, tags
}
```

**Output:**
```typescript
{
  agents: Array<{
    name: string,
    protocols: string[],
    category: string,
    version: string,
    status: string,
    steward: string,
    description: string,
    url: string
  }>,
  count: number,
  data_as_of: string
}
```

### 2. check_protocol_support
Look up which protocols a company supports.

**Input:**
```typescript
{
  company: string   // fuzzy match against deployments.company
}
```

**Output:**
```typescript
{
  company: string,
  protocols: Array<{
    protocol: string,
    use_case: string,
    announced_date: string | null
  }>,
  total_protocols: number,
  data_as_of: string
}
```

### 3. get_protocol_metrics
Get adoption metrics for one or all protocols.

**Input:**
```typescript
{
  protocol?: string   // omit for all protocols
}
```

**Output:**
```typescript
{
  metrics: Array<{
    protocol: string,
    github_stars: number,
    npm_weekly_downloads: number,
    pypi_weekly_downloads: number,
    contributors: number,
    maturity: string,
    momentum_30d_pct: number | null
  }>,
  data_as_of: string
}
```

### 4. find_deployments
Search the deployment directory.

**Input:**
```typescript
{
  protocol?: string,
  country?: string,    // ISO 3166-1 alpha-2
  category?: string,
  search?: string,     // company name search
  limit?: number       // default 20, max 100
}
```

**Output:**
```typescript
{
  deployments: Array<{
    company: string,
    protocol: string,
    country: string | null,
    region: string | null,
    category: string | null,
    use_case: string | null,
    announced_date: string | null
  }>,
  total: number,
  data_as_of: string
}
```

### 5. get_compatibility
Check if two protocols can interoperate.

**Input:**
```typescript
{
  protocol_a: string,
  protocol_b: string
}
```

**Output:**
```typescript
{
  protocol_a: string,
  protocol_b: string,
  compatible: boolean,
  relationship: "native" | "compatible" | "complementary" | "no_direct_bridge",
  bridge_mechanism: string | null,
  notes: string,
  data_as_of: string
}
```

Hardcoded compatibility matrix:
- AdCP + MCP: native. "AdCP is built on MCP as its transport layer. All AdCP servers are MCP servers."
- AdCP + A2A: native. "AdCP uses A2A for agent-to-agent negotiation. Multi-party deal flows use A2A."
- ARTF + MCP: compatible. "ARTF containers expose MCP tool interfaces. An MCP client can invoke ARTF agents."
- ARTF + A2A: compatible. "ARTF supports A2A for inter-container communication."
- Agentic Audiences + MCP: compatible. "Embedding vectors exchanged via MCP tool calls."
- AdCP + ARTF: complementary. "Different layers: AdCP handles campaign workflow, ARTF handles bid-time execution. Both can run in the same campaign."
- AdCP + Agentic Audiences: complementary. "AdCP Signals Activation Protocol can consume Agentic Audiences embeddings."
- ARTF + Agentic Audiences: compatible. "ARTF containers can process Agentic Audiences embedding vectors at bid time."
- A2A + Agentic Audiences: no_direct_bridge. "A2A handles agent communication, Agentic Audiences handles signal encoding. Connected via agents that implement both."
- MCP + A2A: complementary. "MCP connects agents to tools, A2A connects agents to agents. Most production systems use both."

### 6. recommend_stack
Recommend agents and protocols for a campaign goal.

**Input:**
```typescript
{
  goal: string,        // e.g. "programmatic CTV campaign"
  market?: string,     // e.g. "France", "US", "Germany"
  budget?: string,     // e.g. "50K EUR"
  category?: string    // e.g. "Media Trading"
}
```

**Output:**
```typescript
{
  recommendation: string,           // 2-3 sentence summary
  suggested_protocols: string[],    // ranked
  suggested_agents: Array<{
    name: string,
    protocol: string,
    role: string                    // what it does in this stack
  }>,
  market_coverage: {
    deployments_in_market: number,
    top_protocol: string
  },
  reasoning: string,                // why this stack
  data_as_of: string
}
```

Rule-based logic:
1. If market specified, filter deployments by country, identify dominant protocol
2. Match category to relevant agents in marketplace
3. Rank protocols by adoption (metrics) in that market
4. Assemble recommendation from available agents + deployment coverage

### 7. get_market_news
Get latest agentic advertising news.

**Input:**
```typescript
{
  protocol?: string,
  category?: string,
  days?: number,       // default 7
  limit?: number       // default 10, max 50
}
```

**Output:**
```typescript
{
  articles: Array<{
    title: string,
    source: string,
    url: string,
    category: string | null,
    protocols: string[],
    published: string | null
  }>,
  count: number,
  data_as_of: string
}
```

## File Structure

```
/var/www/pievra-mcp/
  package.json
  tsconfig.json
  ecosystem.config.js          # PM2 config
  src/
    index.ts                   # Entry point: parse args, start stdio or SSE
    server.ts                  # MCP server setup, tool registration
    tools/
      discover-agents.ts       # Tool 1
      check-protocol-support.ts # Tool 2
      get-protocol-metrics.ts  # Tool 3
      find-deployments.ts      # Tool 4
      get-compatibility.ts     # Tool 5
      recommend-stack.ts       # Tool 6
      get-market-news.ts       # Tool 7
    data/
      hosted-provider.ts       # SQLite reader (hosted mode)
      local-provider.ts        # JSON snapshot reader (local mode)
      types.ts                 # Shared types
      compatibility-matrix.ts  # Hardcoded protocol relationships
      snapshot.json            # Bundled data (for npm package)
    api/
      snapshot-handler.ts      # GET /mcp/api/snapshot endpoint
  scripts/
    migrate-agents.ts          # One-time: extract AGENTS from marketplace.html to SQLite
    generate-snapshot.ts       # Generate data-snapshot.json from SQLite
  tests/
    tools.test.ts              # Tool logic tests
    data-provider.test.ts      # Data access tests

/etc/nginx/sites-enabled/
  pievra.com                   # MODIFY: add /mcp proxy to port 3004
```

## Deployment

- PM2 process `pievra-mcp` on port 3004
- nginx: `location /mcp { proxy_pass http://127.0.0.1:3004; }` (in sites-enabled)
- npm publish as `@pievra/mcp-server`
- Snapshot regenerated by cron every 6 hours

## MCP Client Configuration

### Claude Desktop / Cursor
```json
{
  "mcpServers": {
    "pievra": {
      "command": "npx",
      "args": ["@pievra/mcp-server"]
    }
  }
}
```

### Remote SSE Connection
```json
{
  "mcpServers": {
    "pievra": {
      "url": "https://pievra.com/mcp"
    }
  }
}
```
