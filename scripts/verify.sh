#!/usr/bin/env bash
set -euo pipefail

MODE="limited"
case "${1:-}" in
  --limited|"")
    MODE="limited"
    ;;
  --full)
    MODE="full"
    ;;
  --demo)
    MODE="demo"
    ;;
  --acceptance)
    MODE="acceptance"
    ;;
  *)
    echo "Usage: bash scripts/verify.sh [--limited|--full|--demo|--acceptance]" >&2
    exit 2
    ;;
esac

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[verify] Mode: $MODE"
echo "[verify] Checking required harness files"
required_files=(
  "AGENTS.md"
  "docs/ARCHITECTURE.md"
  "docs/POLICY_SCHEMA.md"
  "docs/RULE_ENGINE.md"
  "docs/RECOMMENDATION_RULES.md"
  "docs/TEST_SCENARIOS.md"
  "docs/DEVELOPMENT_SETUP.md"
  "tasks/feature_list.json"
  "tasks/progress.md"
  "scripts/verify.sh"
  "scripts/verify.ps1"
  "scripts/run_recommendation_acceptance.py"
  "scripts/run_recommendation_smoke.py"
  "scripts/write_verification_report.py"
  ".env.example"
  "requirements-dev.txt"
)

for file in "${required_files[@]}"; do
  if [ ! -f "$file" ]; then
    echo "[verify] Missing required file: $file" >&2
    exit 1
  fi
done

echo "[verify] Validating task JSON"
python -m json.tool tasks/feature_list.json >/dev/null

echo "[verify] Checking existing tests are present"
mapfile -t test_files < <(find match_agent_v0.8/match_agent_v0.8 -maxdepth 1 -name 'test_*.py' | sort)
test_count="${#test_files[@]}"
if [ "$test_count" -lt 1 ]; then
  echo "[verify] No existing Python tests found" >&2
  exit 1
fi
echo "[verify] Found $test_count Python test files"

is_db_dependent_test() {
  case "$(basename "$1")" in
    test_db_connection.py|test_policy_load.py|test_recommendation_history_service.py)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

run_test_file() {
  local test_file="$1"
  echo "[verify] Running $(basename "$test_file")"
  (cd match_agent_v0.8/match_agent_v0.8 && python "$(basename "$test_file")")
}

if [ "$MODE" = "full" ]; then
  echo "[verify] Running full Python test set"
  if ! python -c "import pytest" >/dev/null 2>&1; then
    echo "[verify] Full mode requires pytest. Install with: python -m pip install -r requirements-dev.txt" >&2
    exit 1
  fi
  (cd match_agent_v0.8/match_agent_v0.8 && python -m pytest)
elif [ "$MODE" = "limited" ] || [ "$MODE" = "acceptance" ]; then
  echo "[verify] Running limited Python test set"
  for test_file in "${test_files[@]}"; do
    if is_db_dependent_test "$test_file"; then
      echo "[verify] Skipping $(basename "$test_file"): DB-dependent test; limited mode does not require SQLAlchemy/PostgreSQL"
      continue
    fi
    run_test_file "$test_file"
  done
else
  echo "[verify] Skipping limited Python test set: demo mode runs frontend build plus acceptance/E2E only"
fi

if [ -d "match_agent_v0.8/match_agent_v0.8/frontend/node_modules" ]; then
  if command -v npm >/dev/null 2>&1; then
    echo "[verify] Running frontend build"
    (cd match_agent_v0.8/match_agent_v0.8/frontend && npm run build)
  else
    echo "[verify] Skipping frontend build: npm is not available"
  fi
else
  echo "[verify] Skipping frontend build: frontend node_modules not found"
fi

if [ "$MODE" = "demo" ] || [ "$MODE" = "acceptance" ]; then
  echo "[verify] Running backend acceptance"
  python scripts/run_recommendation_acceptance.py

  if ! command -v npm >/dev/null 2>&1; then
    echo "[verify] Frontend E2E requires npm" >&2
    exit 1
  fi

  if [ ! -d "match_agent_v0.8/match_agent_v0.8/frontend/node_modules" ]; then
    echo "[verify] Frontend E2E requires frontend node_modules. Run npm install in the frontend directory." >&2
    exit 1
  fi

  echo "[verify] Running frontend E2E"
  (cd match_agent_v0.8/match_agent_v0.8/frontend && npm run test:e2e)

  report_args=()
  if [ "$MODE" = "acceptance" ]; then
    report_args+=(--limited-ran)
  fi
  echo "[verify] Writing Markdown verification report"
  python scripts/write_verification_report.py \
    --command "bash scripts/verify.sh --$MODE" \
    --mode "$MODE" \
    "${report_args[@]}"
fi

echo "[verify] OK"
