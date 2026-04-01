# pievra.

**The intelligence layer for agentic advertising.**

We track every AI agent protocol in programmatic advertising, so yours don't have to.

[![Website](https://img.shields.io/badge/pievra.com-live-F97316?style=flat-square)](https://pievra.com)
[![MCP Server](https://img.shields.io/badge/MCP_Server-live-065f46?style=flat-square)](https://pievra.com/news/mcp)
[![Agents](https://img.shields.io/badge/agents_tracked-27-1d4ed8?style=flat-square)](https://pievra.com/marketplace)
[![Deployments](https://img.shields.io/badge/deployments-73+-5b21b6?style=flat-square)](https://pievra.com/news/analytics)

---

### What we do

Pievra is the neutral hub for the agentic advertising ecosystem. Five protocols are competing to define how AI agents buy and sell media. We track all of them.

| Protocol | Steward | Status |
|----------|---------|--------|
| **AdCP** | AgenticAdvertising.org | 3.0-beta |
| **MCP** | Linux Foundation (Anthropic) | Stable |
| **A2A** | Linux Foundation (Google) | v0.3 Stable |
| **ARTF** | IAB Tech Lab | v1.0 Final |
| **Agentic Audiences** | IAB Tech Lab (LiveRamp) | Phase 1 Draft |

### Products

**[Marketplace](https://pievra.com/marketplace)** - Directory of 27 AI agents across all 5 protocols. Search by protocol, category, status.

**[News](https://pievra.com/news)** - Aggregated feed from 8 adtech publications. Auto-categorized, protocol-tagged, filterable.

**[Analytics](https://pievra.com/news/analytics)** - Live adoption dashboard. GitHub stars, npm downloads, geographic deployments, trend charts.

**[Reports](https://pievra.com/news/reports)** - Original deep-dives on each protocol. Verified facts, pros/cons, real deployment data.

**[MCP Server](https://pievra.com/news/mcp)** - 7 tools your AI agents can call for protocol intelligence. Connect via SSE or stdio.

### Connect your agent

```json
{
  "mcpServers": {
    "pievra": {
      "url": "https://pievra.com/mcp/"
    }
  }
}
```

Your agent gets: `discover_agents`, `check_protocol_support`, `get_protocol_metrics`, `find_deployments`, `get_compatibility`, `recommend_stack`, `get_market_news`

### Repos

| Repo | What | Stack |
|------|------|-------|
| [**pievra**](https://github.com/pievra/pievra) | Static site, marketplace, all pages | HTML/CSS/JS |
| [**pievra-news**](https://github.com/pievra/pievra-news) | News feed, analytics dashboard, reports, admin | Next.js 16, Recharts, SQLite |
| [**pievra-mcp**](https://github.com/pievra/pievra-mcp) | MCP server (7 tools, SSE + stdio) | TypeScript, MCP SDK, SQLite |

### License

MIT
