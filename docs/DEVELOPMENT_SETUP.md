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

Frontend E2E uses Playwright. It was added as a frontend dev dependency because the demo screen must be verified in a real browser, including route loading, button interaction, visible result text, forbidden wording checks, and screenshot capture.

Install frontend dependencies:

```powershell
cd match_agent_v0.8\match_agent_v0.8\frontend
npm.cmd install
npx.cmd playwright install chromium
```

## DB-Dependent Tests

The following existing tests depend on SQLAlchemy and/or PostgreSQL connectivity:

- `test_db_connection.py`
- `test_policy_load.py`
- `test_recommendation_history_service.py`

Limited verification skips these tests and prints the skip reason. Full verification runs them and must fail if dependencies or DB connectivity are not available.

## Status Updates

Only mark a feature `passing` in `tasks/feature_list.json` after the relevant verification mode passes. Record the exact command and result in `tasks/progress.md`.
