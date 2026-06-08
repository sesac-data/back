# Incentdoc v2 Agent Guide

## Scope

This repository is the Incentdoc v2 planning and implementation workspace.

Do not implement product features unless the task explicitly asks for implementation. Do not change existing business logic when working on harness, documentation, verification, or planning tasks.

## Required Reading

- `docs/ARCHITECTURE.md`
- `docs/POLICY_SCHEMA.md`
- `docs/RULE_ENGINE.md`
- `docs/RECOMMENDATION_RULES.md`
- `docs/TEST_SCENARIOS.md`
- `docs/analysis/CURRENT_STATE.md`
- `docs/analysis/GAP_ANALYSIS.md`
- `docs/analysis/IMPLEMENTATION_ORDER.md`

## Operating Rules

- LLM usage is limited to policy source extraction and candidate condition structuring.
- Eligibility, amount calculation, duplicate-benefit handling, and recommendation optimization must be code based.
- Use only human-approved policy structures for recommendation calculation.
- General companies and labor partners operate independently in the MVP.
- Do not build company-to-labor-partner matching in the MVP.
- Do not delete or weaken existing tests.
- Run `scripts/verify.sh` after each feature implementation.
- Mark a feature `passing` in `tasks/feature_list.json` only after verification passes.
- Append all work results to `tasks/progress.md`.

## Task Ledger

- `tasks/feature_list.json`
- `tasks/progress.md`

