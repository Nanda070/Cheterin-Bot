---
type: "query"
date: "2026-07-16T16:17:07.417785+00:00"
question: "Why does SelectOption connect Mafia Game Engine to Discord Embed Builder, Supply Cog Tests?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["SelectOption", "Mafia Game Engine", "Discord Embed Builder", "Supply Cog Tests"]
---

# Q: Why does SelectOption connect Mafia Game Engine to Discord Embed Builder, Supply Cog Tests?

## Answer

The name SelectOption exists in both Python (as discord.SelectOption) and React (as SelectOption component). The extractors mapped both to the same ID, creating a name clash/bridge node that connects the backend Discord cogs (Mafia, Supply) to the frontend React UI select components.

## Outcome

- Signal: useful

## Source Nodes

- SelectOption
- Mafia Game Engine
- Discord Embed Builder
- Supply Cog Tests