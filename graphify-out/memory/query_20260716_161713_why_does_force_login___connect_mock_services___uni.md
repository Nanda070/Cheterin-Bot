---
type: "query"
date: "2026-07-16T16:17:13.336142+00:00"
question: "Why does force_login() connect Mock Services & Unit Tests to a wide array of system modules and tests?"
contributor: "graphify"
outcome: "useful"
source_nodes: ["force_login()", "Mock Services & Unit Tests"]
---

# Q: Why does force_login() connect Mock Services & Unit Tests to a wide array of system modules and tests?

## Answer

The force_login() function is a fundamental helper defined in dashboard/backend/tests/fakes.py. It is used to mock a logged-in dashboard user across 252 tests in the backend, connecting them to various route and module test files.

## Outcome

- Signal: useful

## Source Nodes

- force_login()
- Mock Services & Unit Tests