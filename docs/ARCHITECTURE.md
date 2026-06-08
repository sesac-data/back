# Incentdoc v2 Architecture

## Purpose

Incentdoc v2 manages employment-support policy operations for two independent MVP user types:

- `general_company`: A company manages its own employees, leave events, documents, deadlines, expected subsidy amounts, and replacement hiring tasks.
- `labor_partner`: A labor law firm or labor partner manages multiple client companies, their employees, document review status, newsletters, and partner settings.

The MVP must not connect, match, or automatically share data between general companies and labor partners.

## Current Repository Shape

The repository currently contains two product surfaces and a policy/recommendation core:

- Streamlit app: `match_agent_v0.8/match_agent_v0.8/app.py`
- React/Vite prototype: `match_agent_v0.8/match_agent_v0.8/frontend/src/App.jsx`
- Policy and recommendation services: `match_agent_v0.8/match_agent_v0.8/services/`
- Database models and CRUD helpers: `match_agent_v0.8/match_agent_v0.8/database/`
- Policy JSON fixtures: `match_agent_v0.8/match_agent_v0.8/data/policy_json/`

The existing code already contains policy extraction, condition evaluation, amount calculation, and recommendation-selection code. It does not yet contain a complete v2 domain model for users, user types, organizations, client companies, employees, leave events, documents, deadlines, notifications, or approvals.

## Target Boundaries

The product should be organized around these boundaries:

```text
accounts
  users
  user_type
  permissions

organizations
  general_company
  labor_partner
  client_company

people
  employees
  leave_events

policies
  source_documents
  structured_policy_versions
  review_status

engine
  rule_engine
  amount_calculator
  duplicate_rules
  recommendation_optimizer

operations
  documents
  deadlines
  notifications
  newsletters
  replacement_hiring
```

## Data Ownership

Data ownership must be explicit.

For a general company:

```text
user -> general_company -> employee -> leave_event
```

For a labor partner:

```text
user -> labor_partner -> client_company -> employee -> leave_event
```

No MVP feature may imply this relationship:

```text
general_company <-> labor_partner
```

That connection is out of scope until a future explicit matching or consent model is designed.

## Policy Processing Pipeline

Policy processing is split into human-reviewable stages:

1. Policy source collection
2. LLM-assisted source extraction
3. Candidate structured policy JSON
4. Human review
5. Approved policy version
6. Code-based rule evaluation
7. Code-based amount calculation
8. Code-based duplicate-benefit and combination optimization
9. Recommendation result storage

Only approved policy versions can be used in recommendation calculation.

## LLM Boundary

LLMs may only perform:

- Policy source text extraction assistance
- Candidate condition structure generation
- Evidence snippet collection from policy source text

LLMs must not decide:

- Final eligibility
- Final amount
- Duplicate-benefit compatibility
- Recommendation ranking
- Combination optimization
- Missing policy requirements not present in source text

## Verification Boundary

The harness is centered on `scripts/verify.sh`.

The script should verify at minimum:

- Required harness files exist.
- `tasks/feature_list.json` is valid JSON.
- Existing tests are still discoverable and runnable when the local environment supports them.
- Frontend build can run when frontend dependencies are already available.

No feature should be marked `passing` in `tasks/feature_list.json` unless `scripts/verify.sh` passes for that feature's relevant scope.

## Automated Demo Verification Flow

The verification harness now has a demo/acceptance path for deterministic backend and frontend checks.

```text
data/acceptance_scenarios/*.json
  -> scripts/run_recommendation_acceptance.py
  -> existing calculation_service functions
  -> existing policy_combination_generator
  -> existing combination_amount_summarizer
  -> output/verification/backend-report.json

frontend Playwright E2E
  -> Vite preview /company/recommendation-demo
  -> UI assertions and screenshot
  -> output/verification/frontend-report.json
  -> output/verification/frontend-screenshot.png

scripts/verify.ps1 -Mode demo|acceptance
  -> frontend build
  -> backend acceptance
  -> frontend E2E
  -> output/verification/latest-report.md
```

This flow is a harness only. It does not change policy formulas, combination generation rules, frontend UI structure, API boundaries, mock adapter data, or database schema.

## Frontend Recommendation Demo Boundary

The React/Vite frontend now includes a general-company-only recommendation demo screen for team sharing.

- Demo path: `/company/recommendation-demo`
- In-app view key: `recommendationDemo`
- Component location: `match_agent_v0.8/match_agent_v0.8/frontend/src/App.jsx`
- Data service: `match_agent_v0.8/match_agent_v0.8/frontend/src/services/recommendationService.js`
- Current adapter: `match_agent_v0.8/match_agent_v0.8/frontend/src/services/mockRecommendationAdapter.js`

The demo screen is intentionally a presentation layer over the current recommendation result shape. It does not duplicate backend eligibility, amount, combination, or optimization logic in the frontend.

Current integration behavior:

- The component calls `fetchGeneralCompanyRecommendationDemo`.
- The service delegates to the active adapter.
- The active adapter is mock-based because there is no callable recommendation API endpoint in the React app yet.
- The component consumes a structure aligned with `combination_amount_summarizer` output: `summarized_combinations`, `rejected_combinations`, policy-level calculation summaries, `calculation_steps`, and `evidence_snippets`.
- The mock adapter can later be replaced with an API adapter without changing the screen component contract.

The demo must not describe results as "optimal recommendations" or "best combinations." Until optimizer and ranking logic exists, the UI should use comparison language such as "지원금 조합 비교" and "가장 높은 총지원금".
