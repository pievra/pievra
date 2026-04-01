# Pievra

The open marketplace for agentic advertising. Every AI agent, every protocol, one platform.

**Live at [pievra.com](https://pievra.com)**

## What is Pievra?

Pievra is the neutral intelligence hub for the agentic advertising ecosystem. We track, index, and analyze every protocol and agent across AdCP, MCP, Agentic Audiences (UCP), ARTF, and A2A.

## Architecture

| Component | Repo | URL |
|-----------|------|-----|
| **Static Site** | [pievra/pievra](https://github.com/pievra/pievra) (this repo) | [pievra.com](https://pievra.com) |
| **News + Analytics** | [pievra/pievra-news](https://github.com/pievra/pievra-news) | [pievra.com/news](https://pievra.com/news) |
| **MCP Server** | [pievra/pievra-mcp](https://github.com/pievra/pievra-mcp) | [pievra.com/mcp](https://pievra.com/news/mcp) |

## Pages

- **/** - Homepage
- **/marketplace** - Agent directory (26 agents across 5 protocols)
- **/news** - Protocol news feed with RSS aggregation, category filters, protocol tags
- **/news/analytics** - Live protocol adoption dashboard (GitHub stars, npm downloads, 73+ deployments)
- **/news/reports** - Original protocol deep-dives (AdCP, MCP, ARTF, A2A, Agentic Audiences)
- **/news/mcp** - MCP Server developer documentation
- **/partners** - Partner directory
- **/careers** - Open positions

## Tech Stack

- Static HTML/CSS/JS (this repo)
- Next.js 16 + Tailwind CSS 4 (pievra-news)
- MCP Server with SSE + stdio (pievra-mcp)
- SQLite databases
- Python data collectors (RSS feeds, GitHub/npm metrics)
- PM2 process management
- nginx reverse proxy

## License

MIT
