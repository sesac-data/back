# Development Setup

## Verification Modes

The project has four verification modes.

### Limited Verification

Use this when the local machine does not have database test dependencies or a running PostgreSQL test database.

Limited verification:

- Checks required harness files.
- Validates `tasks/feature_list.json`.
- Confirms existing Python tests are still present.
- Runs non-DB Python tests.
- Skips DB-dependent tests with an explicit reason.
- Runs the frontend build when `node_modules` and npm are available.

### Full Verification

Use this when the full Python and database test environment is installed.

Full verification:

- Runs all Python tests, including DB-dependent tests.
- Does not treat missing DB dependencies as passing.
- Requires the database dependencies listed in `requirements-dev.txt`.
- Requires a reachable PostgreSQL database matching the current project DB configuration.
- Runs the frontend build when `node_modules` and npm are available.

### Demo Verification

Use this to automatically verify the backend recommendation acceptance scenarios and the React recommendation demo screen without running the full limited Python test set.

Demo verification:

- Runs the frontend build.
- Runs backend acceptance scenarios through `scripts/run_recommendation_acceptance.py`.
- Runs Playwright E2E for `/company/recommendation-demo`.
- Writes `output/verification/backend-report.json`.
- Writes `output/verification/frontend-report.json`.
- Writes `output/verification/frontend-screenshot.png`.
- Writes `output/verification/latest-report.md`.

### Acceptance Verification

Use this when you want the limited regression suite plus the backend acceptance and frontend E2E checks in one command.

Acceptance verification:

- Runs everything from limited verification.
- Runs backend acceptance scenarios.
- Runs frontend E2E.
- Writes the combined Markdown report.

## Windows PowerShell Commands

Run limited verification:

```powershell
.\scripts\verify.ps1 -Mode limited
```

Run full verification:

```powershell
.\scripts\verify.ps1 -Mode full
```

Run demo verification:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode demo
```

Run acceptance verification:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode acceptance
```

Run the offline policy extraction evaluation harness:

```powershell
python scripts\run_policy_extraction_eval.py
```

The harness reads test-only fixtures from `data/policy_extraction_eval/` and writes:

```text
output/policy_extraction_eval/latest-report.json
output/policy_extraction_eval/latest-report.md
```

It does not call a live LLM API and does not approve or auto-correct candidate policy JSON.

Run live OpenAI policy extraction and evaluate the generated candidates:

```powershell
$env:OPENAI_API_KEY="..."
$env:POLICY_EXTRACTION_MODEL="gpt-4.1-mini"
$env:POLICY_EXTRACTION_PROMPT_VERSION="policy_extraction_v1"
python scripts\run_policy_extraction_llm_eval.py
```

Run repeated live extraction with a prompt-version-selected prompt:

```powershell
python scripts\run_policy_extraction_llm_eval.py --prompt-version policy_extraction_v2 --runs 5
```

When `--prompt-path` is omitted, the runner uses `prompts/{prompt_version}.md` if it exists. If `--prompt-path` is provided, that file is used first. Reports include `prompt_file` and `prompt_sha256`.

If `OPENAI_API_KEY` is missing, the runner exits with a clear error. Do not log or commit real API keys.

The mock fixture runner writes generated candidates and repeated summary reports under:

```text
output/policy_extraction_eval/{prompt_version}/
```

## Real Policy Extraction Evaluation Dataset

The real policy-source evaluation dataset uses separated raw text, metadata, and human-written gold JSON:

```text
data/policy_extraction_real_eval/
├── raw_text/
├── gold/
└── metadata/
```

Each case must use the same file stem:

```text
raw_text/{case_id}.txt
gold/{case_id}.json
metadata/{case_id}.json
```

Metadata must contain:

```json
{
  "case_id": "case_id_matching_file_stem",
  "policy_name": "Human-readable policy name",
  "source_url": "https://example.gov/policy",
  "source_type": "official_page",
  "collected_at": "2026-06-14",
  "notes": "Collection or review notes"
}
```

Run the real policy dataset evaluation:

```powershell
python scripts\run_policy_extraction_llm_eval.py --dataset data\policy_extraction_real_eval --prompt-version policy_extraction_v2 --runs 5
```

Real policy dataset reports are stored separately:

```text
output/policy_extraction_real_eval/{prompt_version}/
```

The runner validates the dataset structure before calling the LLM. Missing `gold/{case_id}.json`, missing `metadata/{case_id}.json`, and missing required metadata fields return clear errors. Generated candidates are not saved to Supabase and are not auto-approved or auto-corrected.

The PowerShell script avoids the Windows `bash.exe` ambiguity where `C:\Windows\System32\bash.exe` launches WSL and fails if no default WSL distro is installed.

## Git Bash Commands

Run limited verification:

```bash
bash scripts/verify.sh --limited
```

Run full verification:

```bash
bash scripts/verify.sh --full
```

Run demo verification:

```bash
bash scripts/verify.sh --demo
```

Run acceptance verification:

```bash
bash scripts/verify.sh --acceptance
```

On Windows, prefer Git Bash explicitly if plain `bash` resolves to WSL:

```powershell
& "C:\Program Files\Git\bin\bash.exe" scripts/verify.sh --limited
```

## Development Dependencies

Install the runtime and development dependencies from the workspace root:

```powershell
python -m pip install -r requirements-dev.txt
```

`requirements-dev.txt` includes:

- Existing app/runtime dependencies from `match_agent_v0.8/match_agent_v0.8/requirements.txt`
- `pytest` for Python test discovery
- `SQLAlchemy` for DB model and DB service tests
- `psycopg2-binary` for PostgreSQL access
- `fastapi` and `uvicorn` for the local demo recommendation HTTP API

Frontend E2E uses Playwright. It was added as a frontend dev dependency because the demo screen must be verified in a real browser, including route loading, button interaction, visible result text, forbidden wording checks, and screenshot capture.

Install frontend dependencies:

```powershell
cd match_agent_v0.8\match_agent_v0.8\frontend
npm.cmd install
npx.cmd playwright install chromium
```

## Demo Recommendation API

Run the local demo recommendation API from the workspace root:

```powershell
python scripts\run_demo_recommendation_api.py
```

Or run the FastAPI app directly from the app directory:

```powershell
cd match_agent_v0.8\match_agent_v0.8
python -m uvicorn api_server:app --reload --host 127.0.0.1 --port 8000
```

The server listens on:

```text
http://127.0.0.1:8000
```

Health endpoint:

```text
GET /health
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Demo endpoint:

```text
POST /api/demo/recommendations/calculate
```

This API uses the approved policy loader boundary in `match_agent_v0.8/match_agent_v0.8/services/approved_policy_loader.py`. The request field `policy_source` accepts only `demo_fixture` or `policy_db`. If omitted, the API keeps the stable default of `demo_fixture` and reads test-only fixture data from `data/acceptance_scenarios/optimal_combination.json`.

Only policies with `review_status == "approved"` are passed to the recommendation orchestration. The demo API does not connect to the policy database or recommendation log storage.

`policy_db` can load approved and active policies from a dedicated PostgreSQL test database when configured. It queries the `subsidy_policies` table with:

```text
review_status = 'approved'
is_active = TRUE
```

Configure a test database only:

```powershell
$env:INCENTDOC_POLICY_DB_URL="postgresql://postgres:postgres@localhost:5432/incentdoc_policy_test"
```

Apply the minimal table migration:

```powershell
psql $env:INCENTDOC_POLICY_DB_URL -f database\migrations\001_create_subsidy_policies.sql
```

Optionally seed calculation-capable test fixture rows. These rows are explicitly not real policies:

```powershell
psql $env:INCENTDOC_POLICY_DB_URL -f database\seeds\001_seed_subsidy_policies_test_fixtures.sql
```

To run the optional real DB loader assertion inside `test_approved_policy_loader.py`:

```powershell
$env:INCENTDOC_RUN_POLICY_DB_INTEGRATION="true"
python match_agent_v0.8\match_agent_v0.8\test_approved_policy_loader.py
```

If `INCENTDOC_RUN_POLICY_DB_INTEGRATION` is not `true`, the real DB assertion prints a skip message. Unit tests still cover DB success and error branches with fake connections.

Minimal request:

```json
{
  "policy_source": "demo_fixture",
  "company": {
    "company_name": "Demo Company",
    "size": "small"
  },
  "employee": {
    "employee_name": "Demo Employee"
  },
  "leave_event": {
    "leave_type": "parental_leave",
    "start_date": "2026-07-01",
    "end_date": "2026-10-31",
    "has_replacement_worker": false
  },
  "employer_cost_items": []
}
```

Frontend default mode remains mock:

```powershell
cd match_agent_v0.8\match_agent_v0.8\frontend
npm.cmd run dev
```

Run the frontend against the demo API:

```powershell
cd match_agent_v0.8\match_agent_v0.8\frontend
$env:VITE_RECOMMENDATION_ADAPTER="api"
$env:VITE_RECOMMENDATION_API_BASE_URL="http://127.0.0.1:8000"
$env:VITE_RECOMMENDATION_POLICY_SOURCE="demo_fixture"
npm.cmd run dev
```

To point API adapter mode at the configured Supabase/PostgreSQL test policy DB, set:

```powershell
$env:VITE_RECOMMENDATION_POLICY_SOURCE="policy_db"
```

In `demo_fixture` mode the screen displays `데모 정책 데이터 기준 결과입니다.`. In `policy_db` mode it displays `Supabase 테스트 정책 DB 기준 결과입니다.`. DB errors are returned as structured API errors and are not hidden by falling back to fixture data.

The local API allows CORS only for the local Vite dev and preview origins used by this project.

## DB-Dependent Tests

The following existing tests depend on SQLAlchemy and/or PostgreSQL connectivity:

- `test_db_connection.py`
- `test_policy_load.py`
- `test_recommendation_history_service.py`

Limited verification skips these tests and prints the skip reason. Full verification runs them and must fail if dependencies or DB connectivity are not available.

## Status Updates

Only mark a feature `passing` in `tasks/feature_list.json` after the relevant verification mode passes. Record the exact command and result in `tasks/progress.md`.
