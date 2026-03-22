// Pievra — Real-Time Analytics Stream Example
// Monitor live campaign performance across all active protocols
// Docs: https://github.com/pievra/pievra

import { PievraSession } from "@pievra/sdk";

const session = new PievraSession({
  apiKey: process.env.PIEVRA_API_KEY,
  sessionId: "psn_01HTXY...",   // Resume an existing session
});

// Open a real-time WebSocket analytics stream
const stream = session.analytics.stream();

// Every impression — fired per delivery event
stream.on("impression", (event) => {
  console.log({
    protocol:    event.protocol,       // "AdCP" | "MCP" | "ARTF" etc.
    agentId:     event.agentId,        // "agt_pubmatic_ctv_001"
    cpm:         event.cpm,            // 16.40
    viewability: event.viewability,    // 0.94
    roas:        event.roasActual,     // 3.2
    timestamp:   event.ts,            // ISO 8601
  });
});

// Budget reallocation — fired when Pievra shifts spend between agents
stream.on("reallocation", (event) => {
  console.log(
    "Reallocated $" + event.amount +
    " from " + event.from +
    " to " + event.to +
    " (reason: " + event.reason + ")"
  );
});

// Protocol switch — fired when a better protocol clears mid-flight
stream.on("protocol_switch", (event) => {
  console.log(
    "Switched from " + event.from +
    " to " + event.to +
    " — CPM delta: " + event.cpmDelta
  );
});

// Export a full report when the campaign ends
session.on("flight_end", async () => {
  const report = await session.analytics.export({
    format: "csv",
    granularity: "hourly",
    metrics: ["cpm", "roas", "viewability", "protocol", "agentId"],
  });
  console.log("Report saved to:", report.path);
});
