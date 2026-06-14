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

## Policy Extraction Evaluation Harness

LLM policy extraction candidates can be evaluated offline before any human approval or runtime recommendation use.

```text
data/policy_extraction_eval/*.json
  -> scripts/run_policy_extraction_eval.py
  -> services/policy_structure_evaluator.py
  -> output/policy_extraction_eval/latest-report.json
  -> output/policy_extraction_eval/latest-report.md
```

This harness compares test-only policy source text, human-written expected JSON, and assumed LLM candidate JSON. It does not call a live LLM API, does not auto-correct candidate JSON, and does not mark any candidate as approved. Candidate fixtures must remain `review_status="needs_review"`.

The evaluator is separate from the Rule Engine and recommendation pipeline. It must not change policy formulas, eligibility evaluation, policy loading, combination generation, API behavior, DB schema, or frontend UI.

Live LLM extraction evaluation is a separate batch harness:

```text
data/policy_extraction_eval/*.json
  -> prompts/policy_extraction_v1.md
  -> services/openai_policy_extraction_adapter.py
  -> services/policy_structure_evaluator.py
  -> output/policy_extraction_eval/generated/
  -> output/policy_extraction_eval/model-comparison-report.json
  -> output/policy_extraction_eval/model-comparison-report.md
```

The live harness calls OpenAI only when `OPENAI_API_KEY` is configured. It stores raw responses and parsed candidates for review, but does not write to the DB, does not auto-repair JSON, and does not approve candidates.

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
- The default active adapter is mock-based for stable local demo behavior.
- API mode can call `POST /api/demo/recommendations/calculate` and can choose `policy_source=demo_fixture|policy_db`.
- The component consumes a structure aligned with `combination_amount_summarizer` output: `summarized_combinations`, `rejected_combinations`, policy-level calculation summaries, `calculation_steps`, and `evidence_snippets`.
- The mock adapter and API adapter share the same screen component contract.

The demo must not describe results as "optimal recommendations" or "best combinations." Until optimizer and ranking logic exists, the UI should use comparison language such as "지원금 조합 비교" and "가장 높은 총지원금".

## Demo Recommendation API Boundary

The general-company recommendation demo can now call a minimal local API for deterministic backend calculation.

- Endpoint: `POST /api/demo/recommendations/calculate`
- Health endpoint: `GET /health`
- FastAPI app: `match_agent_v0.8/match_agent_v0.8/api_server.py`
- Server entry point: `scripts/run_demo_recommendation_api.py`
- Orchestration service: `match_agent_v0.8/match_agent_v0.8/services/demo_recommendation_orchestrator.py`
- Frontend API adapter: `match_agent_v0.8/match_agent_v0.8/frontend/src/services/apiRecommendationAdapter.js`
- Adapter selector: `VITE_RECOMMENDATION_ADAPTER=mock|api`
- Policy source selector: request field `policy_source=demo_fixture|policy_db`
- Default adapter: `mock`

The FastAPI server is a minimal HTTP layer over the existing demo orchestration service. It exposes Swagger UI at `/docs`, allows CORS only for local Vite dev origins `http://127.0.0.1:5173` and `http://localhost:5173`, and does not duplicate calculation logic.

The API is a demo-only orchestration layer over the existing backend services:

```text
HTTP request
  -> request schema validation
  -> approved policy loader
  -> selected source: test-only demo fixture or policy_db
  -> approved policy calculation
  -> standardized policy result normalization
  -> valid/rejected policy combination generation
  -> combination amount summarization
  -> explicit employer net-cost calculation
  -> existing optimal-combination selector
  -> response with source meta
```

The API uses `services/approved_policy_loader.py` as the policy source boundary. The loader supports:

- `demo_fixture`: reads `data/acceptance_scenarios/optimal_combination.json` as test fixture data.
- `policy_db`: reads approved and active policy JSON from PostgreSQL `subsidy_policies`.

Both sources return only policies with `review_status == "approved"` before orchestration receives them. The `policy_db` source also requires `is_active = TRUE` at the table row level and verifies that `policy_json.review_status` matches the DB column value. If DB connection, table lookup, JSON parsing, or review-status validation fails, the loader returns structured errors and does not fall back to demo fixtures.

The API does not store recommendation history, implement login or permissions, infer costs, or add production deployment behavior.

Response metadata must identify the data boundary:

```json
{
  "meta": {
    "data_source": "demo_fixture",
    "is_demo": true,
    "policy_source": {
      "data_source": "demo_fixture",
      "is_demo": true,
      "fixture": "optimal_combination"
    },
    "loaded_policy_count": 2
  }
}
```

When the request contains `"policy_source": "policy_db"`, the API uses the same approved policy loader `policy_db` path and returns metadata such as:

```json
{
  "meta": {
    "data_source": "policy_db",
    "is_demo": false,
    "policy_source": {
      "data_source": "policy_db",
      "is_demo": false,
      "table": "subsidy_policies"
    },
    "loaded_policy_count": 2
  }
}
```

The frontend does not duplicate backend eligibility, amount, combination, net-cost, or optimal-selection logic. In API mode, it sends the browser input and selected policy source to the API adapter and renders the returned `recommended_combination`, `alternative_combinations`, `rejected_combinations`, `errors`, and `meta`. The screen displays `데모 정책 데이터 기준 결과입니다.` for `demo_fixture` and `Supabase 테스트 정책 DB 기준 결과입니다.` for `policy_db`.

## Rule Engine Domain Adapter Boundary

The demo API now separates domain input normalization from recommendation orchestration.

- Adapter location: `match_agent_v0.8/match_agent_v0.8/services/rule_engine_domain_adapter.py`
- Current scope: general-company demo requests only
- Input: API payload sections `company`, `employee`, and `leave_event`
- Output: deterministic `rule_input`, `requested_months`, and structured `errors`

The adapter maps product/domain-shaped request data into the rule-engine shape consumed by existing calculation services:

```json
{
  "company": {
    "size": "small",
    "has_replacement_worker": true
  },
  "employee": {
    "leave_type": "parental_leave"
  }
}
```

The adapter may calculate request duration from explicit `requested_months` or leave dates, but it must not calculate policy amounts, infer policy conditions, select policies, generate combinations, calculate employer costs, or choose the recommended combination.
