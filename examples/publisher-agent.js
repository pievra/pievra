// Pievra — Publisher Agent Listing Example
// List your SSP inventory as an agent in the Pievra Marketplace
// Docs: https://github.com/pievra/pievra

import { PievraAgent } from "@pievra/sdk";

const agent = new PievraAgent({
  apiKey: process.env.PIEVRA_API_KEY,
  name: "Premium CTV Inventory Agent",
  protocols: ["AdCP", "ARTF"],   // Protocols this agent supports
  inventory: {
    type: "CTV",
    dailyImpressions: 4_200_000,
    floorCPM: 18.50,
    geos: ["US", "UK", "DE", "FR"],
    contentCategories: ["news", "entertainment", "sports"],
  },
  benchmarks: {
    viewability: 0.94,
    completionRate: 0.88,
    brandSafety: "IAS-verified",
    invalidTraffic: "< 0.5%",
  },
});

// List the agent — triggers SDK verification and benchmark validation
const listing = await agent.list();

console.log("Agent ID:", listing.agentId);
console.log("Status:", listing.status);          // "verified" | "pending"
console.log("Marketplace URL:", listing.url);     // pievra.com/marketplace/...
console.log("Protocols active:", listing.protocols);
console.log("Estimated daily queries:", listing.estimatedDailyQueries);
