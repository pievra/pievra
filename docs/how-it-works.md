# How Pievra Works — Technical Documentation

## Overview

Pievra is a protocol-neutral orchestration layer for AI agent-driven programmatic advertising. It sits between campaign planners (buyers, agencies) and AI agents (DSPs, SSPs, data providers) and handles protocol translation, auction orchestration and performance analytics — all in a single session call.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         BUYER / AGENCY                           │
│           Campaign brief — objective, budget, audience           │
└──────────────────────────────┬───────────────────────────────────┘
                               │  PievraSession.execute()
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                      PIEVRA ORCHESTRATOR                         │
│                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ Protocol Router │  │  Matching Engine  │  │ Analytics Bus  │  │
│  │                 │  │                  │  │                │  │
│  │ Translates bid  │  │ Cross-protocol   │  │ Streams ROAS,  │  │
│  │ requests into   │  │ arbitrage and    │  │ CPM delta and  │  │
│  │ each protocol's │  │ agent ranking    │  │ agent perf     │  │
│  │ native format   │  │ by objective     │  │ benchmarks     │  │
│  └────────┬────────┘  └────────┬─────────┘  └───────┬────────┘  │
│           │                   │                     │            │
└───────────┼───────────────────┼─────────────────────┼────────────┘
            │                   │                     │
     ┌──────┴──────┐    ┌───────┴──────┐    ┌────────┴───────┐
     │             │    │              │    │                │
     ▼             ▼    ▼              ▼    ▼                ▼
  AdCP           MCP   ARTF           UCP  A2A         Analytics
  Agents        Agents Agents        Agents Agents       Store
     │             │    │              │    │
     └──────────────────┴──────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  PUBLISHER /    │
              │  SSP / DATA     │
              │  PROVIDER       │
              └─────────────────┘
```

---

## Step 1 — Campaign Definition (5 minutes)

### What happens

The buyer creates a `PievraSession` with campaign parameters. Pievra's protocol router analyses the configuration and determines which protocols are compatible with the objectives.

### Input parameters

| Parameter | Type | Description |
|---|---|---|
| `protocols` | `string[]` | Protocol stack — or `['auto']` to let Pievra select |
| `budget` | `number` | Total campaign budget in USD |
| `objective` | `string` | Primary KPI — `ROAS > 2.8`, `CPA < 15`, `CPM < 4.50` |
| `audience` | `object` | Targeting parameters — first-party, contextual, UCP segments |
| `environments` | `string[]` | `web`, `ctv`, `dooh`, `audio` |
| `flight` | `object` | Start and end dates |

### Agent listing (SSP / publisher side)

Agents are submitted to the Pievra Marketplace via the SDK verification flow:

1. **SDK integration** — agent declares protocol compatibility
2. **Performance benchmarking** — verified CPM, fill rate, ROAS baselines
3. **Listing approval** — Pievra compliance review (typically 24 hours)
4. **Live activation** — agent becomes available in real-time matching

```javascript
// Agent declaration example
const agent = new PievraAgent({
  name: 'OpenWeb Contextual Agent v3',
  protocols: ['AdCP', 'MCP'],
  inventory_type: 'contextual_display',
  environments: ['web'],
  benchmarks: {
    avg_cpm: 3.20,
    fill_rate: 0.87,
    viewability: 0.72,
  }
});

await agent.register(); // Triggers SDK verification flow
```

---

## Step 2 — Live Auction Orchestration

### What happens

Once a session is executed, Pievra runs parallel auction requests across all compatible agents simultaneously. This is the core differentiation — all five protocols are called in a single round trip.

### Sequence

```
t=0ms     PievraSession.execute() called
t=2ms     Protocol Router translates brief → 5 native bid requests
t=5ms     Parallel auction calls dispatched to all registered agents
t=45ms    Bid responses collected from all responding agents
t=48ms    Cross-protocol arbitrage runs — ranks by objective (ROAS, CPA, CPM)
t=50ms    Top N agents selected, unified response returned
t=52ms    Analytics event emitted to Analytics Bus
```

### Cross-protocol arbitrage

The matching engine normalises bids across protocols into a unified scoring model:

```
Score = (objective_probability × weight_objective)
      + (cpm_efficiency × weight_efficiency)
      + (historical_performance × weight_historical)
      + (protocol_diversity_bonus)
```

Protocol diversity bonus rewards selecting agents from different protocols, reducing single-protocol dependency risk.

### Liquidity Fee

A 0.75% liquidity fee is applied to all GMV transacted through the platform. This is invoiced monthly in arrears.

---

## Step 3 — Execution and Analytics

### What happens

Matched agents execute the campaign against their inventory. Pievra streams real-time performance data to the Analytics Bus, which powers the dashboard and API.

### Analytics dimensions

| Metric | Description |
|---|---|
| `roas` | Return on ad spend — rolling 24h |
| `cpm_delta` | CPM vs single-protocol baseline (%) |
| `protocol_breakdown` | Spend, impressions, ROAS per protocol |
| `agent_performance` | Per-agent benchmarks vs declared baseline |
| `fill_rate` | Bid response rate per agent |
| `cross_protocol_lift` | ROAS uplift from multi-protocol vs single |

### Export and automation

```javascript
// Stream live analytics
campaign.analytics.on('update', (data) => {
  console.log(`ROAS: ${data.roas} | CPM delta: ${data.cpm_delta}`);
});

// Export full report
const report = await campaign.analytics.export({
  format: 'csv',
  granularity: 'hourly',
  dimensions: ['protocol', 'agent', 'environment'],
});

// Automate bid adjustments
campaign.rules.add({
  condition: 'cpm > 5.00',
  action: 'pause_protocol',
  target: 'AdCP',
});
```

---

## Protocol Integration Details

### AdCP (Ad Context Protocol)

- **Version:** v2.5.1 production
- **Steward:** AgenticAdvertising.org
- **Launched:** 15 October 2025
- **Use case:** Agent-to-agent campaign planning and execution
- **Pievra integration:** Full bid request / response cycle, streaming analytics

### MCP (Model Context Protocol)

- **Version:** Spec 2025-11-25
- **Steward:** Linux Foundation AAIF (donated by Anthropic December 2025)
- **Downloads:** 97M+ monthly
- **Use case:** LLM-to-platform tool calls for campaign planning and audience discovery
- **Pievra integration:** Tool server exposing campaign planner, marketplace query, analytics

### UCP / AAMP (Agentic Audiences)

- **Version:** v1.0 public
- **Steward:** IAB Tech Lab (donated by LiveRamp November 2025)
- **Use case:** Standardised audience segment exposure as callable agents
- **Pievra integration:** Segment discovery, activation, consent propagation

### ARTF (Agentic RTB Framework)

- **Version:** v1.0 public comment (January–March 2026)
- **Steward:** IAB Tech Lab
- **Performance claim:** −80% RTB latency vs current OpenRTB
- **Use case:** Agent-native real-time bidding
- **Pievra integration:** Beta — available in sandbox environment

### A2A (Agent-to-Agent)

- **Version:** v1.0.0
- **Steward:** Linux Foundation (donated by Google June 2025)
- **Members:** 150+ organisations
- **Use case:** Cross-platform agent interoperability and task delegation
- **Pievra integration:** Full — cross-protocol campaign coordination

---

## Security and Compliance

- **Authentication:** API key + HMAC request signing
- **Data in transit:** TLS 1.3
- **Data at rest:** AES-256
- **GDPR:** Full compliance — consent propagation across all protocol calls
- **Audit trail:** Every bid request, match and transaction logged with timestamp

---

## Further Reading

- [Protocol Overview](protocols.md)
- [API Reference](api-reference.md)
- [System Architecture](architecture.md)
- [Newsletter Agent](newsletter-agent.md)
- [SDK Quickstart](../sdk/quickstart.md)
