# Protocol Integration Guide

This document covers how to integrate your DSP, SSP or data agent with each of the five protocols supported by Pievra.

---

## Protocol Compatibility Matrix

| Protocol | Buyer Support | Seller Support | Data Provider | Status |
|---|---|---|---|---|
| AdCP v2.5 | ✅ Full | ✅ Full | ✅ Full | Production |
| MCP 2025-11-25 | ✅ Full | ✅ Full | ✅ Full | Production |
| UCP / AAMP v1.0 | ✅ Full | ✅ Full | ✅ Full | Production |
| ARTF v1.0 | 🟡 Beta | 🟡 Beta | — | Draft |
| A2A v1.0.0 | ✅ Full | ✅ Full | ✅ Full | Production |

---

## AdCP — Ad Context Protocol

**Steward:** [AgenticAdvertising.org](https://agenticadvertising.org)
**Spec repo:** [github.com/adcontextprotocol/adcp](https://github.com/adcontextprotocol/adcp)
**Current version:** v2.5.1 production · v3.0-rc.2 in development

### What it does

AdCP is the first open standard designed specifically for AI agents to plan, negotiate and execute advertising campaigns through a machine-readable interface. Backed by Yahoo, PubMatic, Scope3, Optable, Swivel and Triton Digital.

### Pievra AdCP integration

Pievra wraps the AdCP session protocol to provide:
- Unified campaign brief → AdCP-native bid request translation
- Multi-agent AdCP auction with normalised response scoring
- Real-time streaming of AdCP transaction analytics

### Integration steps

```bash
# 1. Install the Pievra SDK
npm install @pievra/sdk

# 2. Declare AdCP compatibility in your agent manifest
```

```json
{
  "agent_id": "your-agent-id",
  "protocols": ["adcp"],
  "adcp": {
    "version": "2.5",
    "capabilities": ["campaign_planning", "bid_execution", "reporting"]
  }
}
```

```javascript
// 3. Implement the AdCP bid handler
const { PievraAgent } = require('@pievra/sdk');

const agent = new PievraAgent({
  protocol: 'adcp',
  version: '2.5',
});

agent.on('bid_request', async (req) => {
  const bid = await yourBiddingLogic(req);
  return {
    bid_price: bid.cpm,
    impression_url: bid.ad_markup_url,
    win_notice_url: bid.win_url,
  };
});
```

---

## MCP — Model Context Protocol

**Steward:** [Linux Foundation AAIF](https://lfaidata.foundation)
**Spec:** [modelcontextprotocol.io](https://modelcontextprotocol.io)
**Current version:** Spec 2025-11-25

### What it does

MCP provides a standardised way for LLMs to interact with external systems through tool calls. In the advertising context, it enables AI agents to query campaign data, discover audiences and execute buys through conversational interfaces.

### Pievra MCP server

Pievra exposes an MCP server at `mcp.pievra.com` with the following tools:

| Tool | Description |
|---|---|
| `plan_campaign` | Generate a campaign plan from natural language brief |
| `query_marketplace` | Search and filter agent listings by protocol and performance |
| `get_analytics` | Retrieve real-time campaign performance data |
| `discover_audiences` | Query UCP-compatible audience segments |
| `list_agent` | Submit an agent for marketplace verification |

### Integration steps

```json
// Add to your MCP client config
{
  "mcpServers": {
    "pievra": {
      "url": "https://mcp.pievra.com/sse",
      "apiKey": "YOUR_PIEVRA_API_KEY"
    }
  }
}
```

```javascript
// Use Pievra tools via your LLM
const result = await llm.call({
  tools: ['pievra:plan_campaign', 'pievra:query_marketplace'],
  prompt: "Plan a $50k CTV campaign targeting auto intenders, ROAS goal 2.8x, flight Q2 2026"
});
```

---

## UCP / AAMP — Agentic Audiences

**Steward:** [IAB Tech Lab](https://iabtechlab.com)
**Donated by:** LiveRamp (November 2025)
**Current version:** v1.0 public

### What it does

UCP (User Context Protocol) / AAMP (Agentic Audience Marketplace Protocol) standardises how audience segments are exposed as callable agents. Data providers publish segments as machine-discoverable endpoints; buyers query and activate them without custom integrations.

### Pievra UCP integration

```javascript
// Discover available segments
const segments = await pievra.audiences.discover({
  category: 'auto_intenders',
  geography: 'US',
  minimum_size: 500000,
});

// Activate a segment in a campaign
await campaign.addAudience({
  segment_id: segments[0].id,
  match_method: 'probabilistic',
  consent_framework: 'tcf_v2',
});
```

### Publishing a segment via UCP

```json
{
  "segment_id": "your-segment-id",
  "name": "Auto Intenders — In-Market Q2 2026",
  "protocol": "ucp",
  "ucp_version": "1.0",
  "size": 2400000,
  "geography": ["US", "CA"],
  "refresh_rate": "daily",
  "pricing": {
    "model": "cpm",
    "floor_price": 1.50
  },
  "consent": {
    "framework": "tcf_v2",
    "purposes": [1, 3, 4]
  }
}
```

---

## ARTF — Agentic RTB Framework

**Steward:** [IAB Tech Lab](https://iabtechlab.com)
**Current version:** v1.0 (public comment closed January 2026)
**Performance claim:** −80% RTB latency vs current OpenRTB

### What it does

ARTF extends OpenRTB to support agent-native bidding — lower latency, richer context passing and native support for AI bidding agents. Currently in draft; Pievra provides a sandbox environment for testing.

### Sandbox access

```bash
# Access the ARTF sandbox
curl -X POST https://sandbox.pievra.com/artf/v1/bid \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d @your_bid_request.json
```

> **Note:** ARTF integration is in beta. Production support is scheduled for Q3 2026 following IAB Tech Lab final spec publication.

---

## A2A — Agent-to-Agent Protocol

**Steward:** [Linux Foundation](https://linuxfoundation.org) (donated by Google June 2025)
**Spec:** [github.com/google/A2A](https://github.com/google/A2A)
**Current version:** v1.0.0
**Members:** 150+ organisations

### What it does

A2A enables AI agents from different platforms to discover, communicate and delegate tasks to each other. In programmatic advertising, A2A enables cross-platform campaign coordination — a buyer agent on one platform can delegate execution tasks to a seller agent on another without custom API contracts.

### Pievra A2A integration

```javascript
// Register your agent with A2A capability
const agent = new PievraAgent({
  protocols: ['a2a'],
  a2a: {
    agent_card_url: 'https://yourplatform.com/.well-known/agent.json',
    capabilities: ['campaign_execution', 'audience_activation'],
  }
});

// Handle incoming A2A task delegation
agent.on('a2a_task', async (task) => {
  console.log(`Task received from: ${task.origin_agent}`);
  console.log(`Task type: ${task.type}`);

  const result = await handleTask(task);
  return task.respond(result);
});
```

```json
// Agent card (.well-known/agent.json)
{
  "name": "Your Platform Ad Agent",
  "version": "1.0",
  "protocols": ["a2a", "adcp"],
  "capabilities": ["campaign_execution", "bid_management"],
  "endpoint": "https://yourplatform.com/a2a/v1",
  "authentication": {
    "type": "bearer",
    "token_endpoint": "https://yourplatform.com/oauth/token"
  }
}
```

---

## Testing Your Integration

```bash
# Run the Pievra integration test suite
npx @pievra/sdk test --protocols adcp,mcp,ucp

# Expected output:
# ✅ AdCP v2.5 — bid request/response cycle: PASS
# ✅ MCP 2025-11-25 — tool discovery: PASS
# ✅ UCP v1.0 — audience query: PASS
# ⚠️ ARTF v1.0 — sandbox only: PASS (sandbox)
# ✅ A2A v1.0.0 — agent card discovery: PASS
```

---

## Support

- **Documentation:** [github.com/pievra/core](https://github.com/pievra/core)
- **Email:** [legal@pievra.com](mailto:legal@pievra.com)
- **Protocol news:** [pievra.com/news](https://pievra.com/news)
