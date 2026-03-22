// Pievra — Basic Campaign Example
// Runs a cross-protocol campaign across AdCP and MCP
// Docs: https://github.com/pievra/pievra

import { PievraSession } from "@pievra/sdk";

const session = new PievraSession({
  apiKey: process.env.PIEVRA_API_KEY,
  protocols: ["AdCP", "MCP"],
  budget: 5000,            // USD
  objective: "CPM < 15",
  audience: {
    segments: ["in-market-auto"],
    identity: "UCP",
  },
  environments: ["display", "CTV"],
  flightDates: {
    start: "2026-04-01",
    end: "2026-04-07",
  },
});

// Execute the cross-protocol auction
const result = await session.execute();

console.log("Session ID:", result.sessionId);
console.log("Winning protocol:", result.winningProtocol);
console.log("CPM cleared: $" + result.cpmCleared);
console.log("vs baseline: $" + result.cpmBaseline);
console.log("Arbitrage saving:", result.arbitrageSaving);
console.log("Agents activated:", result.agentsActivated);
console.log("Impressions booked:", result.impressionsBooked.toLocaleString());
