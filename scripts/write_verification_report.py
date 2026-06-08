import argparse
import json
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "output" / "verification"
BACKEND_REPORT = OUTPUT_DIR / "backend-report.json"
FRONTEND_REPORT = OUTPUT_DIR / "frontend-report.json"
SCREENSHOT_PATH = OUTPUT_DIR / "frontend-screenshot.png"
LATEST_REPORT = OUTPUT_DIR / "latest-report.md"
DB_SKIPPED_TESTS = [
    "test_db_connection.py",
    "test_policy_load.py",
    "test_recommendation_history_service.py",
]


def load_json(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def status_icon(status):
    return "PASS" if status == "PASS" else "FAIL"


def build_backend_section(backend_report):
    lines = ["## Backend Acceptance", ""]

    if not backend_report:
        lines.extend([
            "- FAIL: backend report was not generated.",
            "",
        ])
        return lines

    for scenario in backend_report.get("scenarios", []):
        lines.append(
            f"- {status_icon(scenario.get('status'))}: "
            f"{scenario.get('scenario')}"
        )
        lines.append(
            f"  - expected: `{json.dumps(scenario.get('expected'), ensure_ascii=False)}`"
        )
        lines.append(
            f"  - actual: `{json.dumps(scenario.get('actual'), ensure_ascii=False)}`"
        )
        if scenario.get("failures"):
            lines.append(
                f"  - failures: `{json.dumps(scenario.get('failures'), ensure_ascii=False)}`"
            )

    lines.append("")
    return lines


def build_frontend_section(frontend_report):
    lines = ["## Frontend E2E", ""]

    if not frontend_report:
        lines.extend([
            "- FAIL: frontend report was not generated.",
            f"- Screenshot: `{SCREENSHOT_PATH}`",
            "",
        ])
        return lines

    stats = frontend_report.get("stats", {})
    status = "PASS" if stats.get("unexpected", 0) == 0 else "FAIL"
    lines.extend([
        f"- {status}: Playwright E2E",
        f"- expected: `{stats.get('expected', 0)}`",
        f"- unexpected: `{stats.get('unexpected', 0)}`",
        f"- skipped: `{stats.get('skipped', 0)}`",
        f"- Screenshot: `{SCREENSHOT_PATH}`",
        "",
    ])
    return lines


def write_report(command, mode, limited_ran):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    backend_report = load_json(BACKEND_REPORT)
    frontend_report = load_json(FRONTEND_REPORT)

    pass_items = []
    fail_items = []
    skip_items = []

    if limited_ran:
        pass_items.append("limited Python test set")
        pass_items.append("frontend build")
        skip_items.extend(
            f"{test}: DB-dependent test skipped in limited verification"
            for test in DB_SKIPPED_TESTS
        )

    if backend_report and backend_report.get("status") == "PASS":
        pass_items.append("backend acceptance")
    else:
        fail_items.append("backend acceptance")

    frontend_stats = (frontend_report or {}).get("stats", {})
    if frontend_report and frontend_stats.get("unexpected", 0) == 0:
        pass_items.append("frontend E2E")
    else:
        fail_items.append("frontend E2E")

    overall = "PASS" if not fail_items else "FAIL"

    lines = [
        "# Verification Report",
        "",
        f"- 실행 일시: {datetime.now().isoformat(timespec='seconds')}",
        f"- 실행 명령: `{command}`",
        f"- Mode: `{mode}`",
        f"- 전체 결과: **{overall}**",
        "",
        "## PASS",
        "",
    ]
    lines.extend(f"- {item}" for item in pass_items)
    lines.extend(["", "## FAIL", ""])
    lines.extend(f"- {item}" for item in fail_items)
    if not fail_items:
        lines.append("- 없음")
    lines.extend(["", "## SKIP", ""])
    lines.extend(f"- {item}" for item in skip_items)
    if not skip_items:
        lines.append("- 없음")
    lines.append("")
    lines.extend(build_backend_section(backend_report))
    lines.extend(build_frontend_section(frontend_report))
    lines.extend([
        "## DB Test Skip",
        "",
        "- limited 기반 검증에서는 DB 의존 테스트를 명시적으로 skip합니다." if limited_ran else "- 이 모드에서는 limited 테스트를 실행하지 않았습니다.",
        "",
    ])

    LATEST_REPORT.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    print(str(LATEST_REPORT))

    if overall != "PASS":
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Write combined verification Markdown report."
    )
    parser.add_argument("--command", required=True)
    parser.add_argument("--mode", required=True)
    parser.add_argument("--limited-ran", action="store_true")
    args = parser.parse_args()
    write_report(
        args.command,
        args.mode,
        args.limited_ran,
    )


if __name__ == "__main__":
    main()
