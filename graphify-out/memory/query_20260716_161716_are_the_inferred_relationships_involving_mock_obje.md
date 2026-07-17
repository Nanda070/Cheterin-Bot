---
type: "query"
date: "2026-07-16T16:17:16.478648+00:00"
question: "Are the inferred relationships involving mock objects (FakeMember, FakeGuild, FakeBot, FakeRole) with DashboardConfig and _StubForbidden correct?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["FakeMember", "FakeGuild", "FakeBot", "FakeRole", "DashboardConfig", "_StubForbidden"]
---

# Q: Are the inferred relationships involving mock objects (FakeMember, FakeGuild, FakeBot, FakeRole) with DashboardConfig and _StubForbidden correct?

## Answer

Yes, the relationships are correct in a testing context. In the unit tests, these mock objects are passed to handlers that instantiate DashboardConfig or raise _StubForbidden exceptions, creating a functional co-occurrence.

## Outcome

- Signal: useful

## Source Nodes

- FakeMember
- FakeGuild
- FakeBot
- FakeRole
- DashboardConfig
- _StubForbidden