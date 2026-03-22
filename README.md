# Pievra — Cross-Protocol AI Agent Orchestration

> **Run AI agent campaigns across every programmatic protocol at once.**

Pievra is the protocol-native orchestration layer connecting media buyers, publishers and data providers across all five agentic advertising standards simultaneously — AdCP, MCP, UCP, ARTF and A2A — without rebuilding a single integration.

[![License: MIT](https://img.shields.io/badge/License-MIT-teal.svg)](LICENSE)
[![Protocols](https://img.shields.io/badge/Protocols-5%20live-00C4A7)](docs/protocols.md)
[![AAO Member](https://img.shields.io/badge/AAO-Founding%20Member-0A0E1A)](https://agenticadvertising.org)
[![Live](https://img.shields.io/badge/Live-pievra.com-00C4A7)](https://pievra.com)

---

## How It Works — Three Steps to Cross-Protocol Execution

```
┌─────────────────────────────────────────────────────────────┐
│  1. DEFINE      ──▶   2. MATCH        ──▶   3. EXECUTE      │
│  Campaign brief        Live auction           Real-time ROAS │
│  or agent listing      across protocols       and CPM stream │
│  5 minutes             <100ms                 Continuous     │
└─────────────────────────────────────────────────────────────┘
```

---

### Step 1 — Define Your Campaign or List Your Agent

**Time required: 5 minutes.**

Set your campaign objectives, budget, audience parameters and target environments.
Pievra auto-selects the optimal protocol stack based on inventory availability,
agent performance benchmarks and your stated objective.

**For media buyers and agencies:**

```javascript
const campaign = new PievraSession({
  protocols: ['AdCP', 'MCP', 'A2A', 'UCP', 'ARTF'],
  budget: 50000,
  objective: 'ROAS > 2.8',
  audience: {
    segments: ['in-market-auto', 'hh-income-100k+'],
    identity: 'UCP',
  },
  environments: ['CTV', 'display', 'DOOH'],
  flightDates: { start: '2026-04-01', end: '2026-04-30' },
});
```

**For publishers and SSPs listing an agent:**

```javascript
const agent = new PievraAgent({
  name: 'Premium CTV Inventory Agent',
  protocols: ['AdCP', 'ARTF'],
  inventory: {
    type: 'CTV',
    dailyImpressions: 4_200_000,
    floorCPM: 18.50,
    geos: ['US', 'UK', 'DE'],
  },
  benchmarks: {
    viewability: 0.94,
    completionRate: 0.88,
    brandSafety: 'IAS-verified',
  },
});

await agent.list(); // Verified and live in the Pievra Marketplace
```

**What Pievra does at this stage:**
- Validates protocol compatibility for your objective
- Auto-selects which protocols maximise inventory reach for your audience
- Runs a pre-flight benchmark check against the agent registry
- Generates a `PievraSessionID` for audit and attribution

---

### Step 2 — Pievra Matches Agents via Live Auction

**The eight-arm orchestration layer connects DSP and SSP agents across all
active protocols simultaneously in real time.**

```
                ┌──────────────────────────────────┐
                │      PIEVRA ORCHESTRATOR          │
                │  PievraSession ──▶ Protocol Router│
                └──────────────┬───────────────────┘
                               │
      ┌──────────┬─────────────┼───────────┬──────────┐
      ▼          ▼             ▼           ▼          ▼
   AdCP v2.5   MCP 2025    UCP/AAMP    ARTF v1    A2A v1.0
   Agent-to-   LLM-native  Audience    RTB with   Agent-to-
   agent       context     resolution  AI guards  agent deals
      │          │             │           │          │
      └──────────┴─────────────┴───────────┴──────────┘
                               │
                ┌──────────────▼──────────────────┐
                │         AUCTION RESULT           │
                │  Winning agent + protocol        │
                │  Liquidity fee: 0.75% of GMV     │
                └─────────────────────────────────┘
```

**Protocol responsibilities:**

| Protocol | Role in auction | Version |
|---|---|---|
| **AdCP** | Primary agent-to-agent media buying negotiation | v2.5.1 prod |
| **MCP** | LLM-native context passing for AI-driven buyers | Spec 2025-11-25 |
| **UCP / AAMP** | Audience resolution — first-party segment activation | v1.0 public |
| **ARTF** | Structured RTB bid stream with AI execution guardrails | v1.0 draft |
| **A2A** | Autonomous agent-to-agent negotiation for direct deals | v1.0.0 |

**Cross-protocol arbitrage:**

When inventory exists across multiple protocols, Pievra runs simultaneous auctions
and selects the clearing price that minimises CPM while meeting your ROAS objective.
Early benchmarks show 18–23% CPM reduction versus single-protocol execution.

```javascript
const result = await campaign.execute();

// {
//   sessionId: 'psn_01HTXY...',
//   winningProtocol: 'AdCP',
//   cpmCleared: 14.20,
//   cpmBaseline: 17.80,
//   arbitrageSaving: '20.2%',
//   agentsActivated: 8,
//   impressionsBooked: 2_840_000,
//   estimatedROAS: 3.1,
// }
```

---

### Step 3 — Campaign Executes. Analytics Stream Live.

**Monitor ROAS, CPM delta and agent performance benchmarks across protocols
from a single dashboard. Export or automate.**

```javascript
const stream = campaign.analytics.stream();

stream.on('impression', (event) => {
  console.log({
    protocol:    event.protocol,      // 'AdCP'
    agentId:     event.agentId,       // 'agt_pubmatic_ctv_001'
    cpm:         event.cpm,           // 16.40
    viewability: event.viewability,   // 0.94
    roas:        event.roasActual,    // 3.2
  });
});

stream.on('reallocation', (event) => {
  // Pievra auto-reallocates budget to higher-performing agents
  console.log(`Reallocated $${event.amount} from ${event.from} to ${event.to}`);
});
```

**Dashboard metrics:**

| Metric | Description |
|---|---|
| ROAS | Return on ad spend, updated per impression |
| CPM delta | Actual CPM vs single-protocol baseline |
| Agent benchmark score | Viewability × completion × brand safety composite |
| Protocol utilisation | GMV share per protocol across the flight |
| Fill rate | Impressions delivered vs booked |
| Liquidity fee | 0.75% of GMV, invoiced monthly |

**Export:**

```javascript
const report = await campaign.analytics.export({
  format: 'csv',
  granularity: 'hourly',
  metrics: ['cpm', 'roas', 'viewability', 'protocol'],
});
```

---

## Protocol Versions — Live March 2026

| Protocol | Steward | Version | Status | Repo |
|---|---|---|---|---|
| AdCP | AgenticAdvertising.org | v2.5.1 | 🟢 Production | [adcontextprotocol/adcp](https://github.com/adcontextprotocol/adcp) |
| MCP | Linux Foundation AAIF | Spec 2025-11-25 | 🟢 Production | [modelcontextprotocol/modelcontextprotocol](https://github.com/modelcontextprotocol/modelcontextprotocol) |
| UCP / AAMP | IAB Tech Lab | v1.0 | 🟢 Production | [IABTechLab/agentic-audiences](https://github.com/IABTechLab/agentic-audiences) |
| ARTF | IAB Tech Lab | v1.0 draft | 🟡 Public comment | [IABTechLab/agentic-rtb-framework](https://github.com/IABTechLab/agentic-rtb-framework) |
| A2A | Linux Foundation | v1.0.0 | 🟢 Production | [google/A2A](https://github.com/google/A2A) |

---

## Quick Start

```bash
npm install @pievra/sdk
export PIEVRA_API_KEY=your_key_here
```

```javascript
import { PievraSession } from '@pievra/sdk';

const session = new PievraSession({
  apiKey: process.env.PIEVRA_API_KEY,
  protocols: ['AdCP', 'MCP'],
  budget: 1000,
  objective: 'CPM < 15',
});

const result = await session.execute();
console.log(`Cleared at CPM $${result.cpmCleared} — saved ${result.arbitrageSaving}`);
```

---

## Repository Structure

```
pievra/
├── README.md                    ← You are here
├── docs/
│   ├── architecture.md          ← System architecture
│   ├── protocols.md             ← Protocol reference
│   ├── api-reference.md         ← Full API docs
│   ├── how-it-works.md          ← Extended How It Works
│   └── newsletter-agent.md      ← Autonomous newsletter pipeline
├── sdk/
│   ├── javascript/
│   └── python/
└── examples/
    ├── basic-campaign.js
    ├── publisher-agent.js
    ├── data-provider.js
    └── analytics-stream.js
```

---

## Protocol Intelligence Weekly

Autonomous newsletter tracking all five protocols — every Tuesday at 06:00 CET.

- Drafted by Claude from 12 live sources (6 RSS feeds + NewsAPI + GitHub)
- Zero manual intervention
- GDPR-compliant, one-click unsubscribe

**Subscribe free:** [pievra.com/newsletter](https://pievra.com/newsletter)

---

## Contact

- **Website:** [pievra.com](https://pievra.com)
- **Legal:** legal@pievra.com

*© 2026 Pievra. MIT Licensed. Protocol-neutral. Open core.*
