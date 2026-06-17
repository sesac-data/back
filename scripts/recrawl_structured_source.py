"""Re-crawl in-scope policy pages and store table-structure-preserving source text.

The original crawler stores `get_text()` output, which flattens HTML tables. This
script re-fetches the same source URLs and writes a sibling `{incent_key}_structured.txt`
that keeps tables as Markdown rows (via services.html_table_extractor).

It is non-destructive: it never overwrites the existing `{incent_key}_raw.txt` or
`{incent_key}_meta.json`. Run it explicitly; it is not part of the default pipeline.
"""

import argparse
import json
import sys
from pathlib import Path

import requests


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "match_agent_v0.8" / "match_agent_v0.8"
DOCS_ROOT = APP_DIR / "incent_docs"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from services.html_table_extractor import (  # noqa: E402
    extract_structured_text,
)

CRAWL_ENCODING = "utf-8"
CRAWL_TARGET_CSS = "div.cont_wrap_area"
USER_AGENT = "Mozilla/5.0"

IN_SCOPE_DOCUMENT_IDS = (
    "childcare_flexible_start_support",
    "flexible_work_incent",
    "flexible_work_system_support",
    "parental_leave_reduction_support",
    "replacement_workshare_support",
    "working_hours_reduction_support",
    "worklife_balance_45_support",
)


def recrawl_one(incent_key: str) -> dict:
    docs_folder = DOCS_ROOT / f"{incent_key}_docs"
    meta_path = docs_folder / f"{incent_key}_meta.json"

    if not meta_path.exists():
        return {"incent_key": incent_key, "status": "skip_no_meta"}

    meta = json.loads(meta_path.read_text(encoding=CRAWL_ENCODING))
    url = meta.get("url")
    if not url or url == "none":
        return {"incent_key": incent_key, "status": "skip_no_url"}

    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    response.raise_for_status()
    response.encoding = CRAWL_ENCODING

    structured = extract_structured_text(
        response.text,
        CRAWL_TARGET_CSS,
    )

    table_rows = sum(
        1 for line in structured.splitlines() if line.startswith("|")
    )

    out_path = docs_folder / f"{incent_key}_structured.txt"
    out_path.write_text(structured, encoding=CRAWL_ENCODING)

    return {
        "incent_key": incent_key,
        "status": "ok",
        "url": url,
        "char_count": len(structured),
        "table_row_count": table_rows,
        "output": str(out_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Re-crawl in-scope policy pages with table structure preserved."
    )
    parser.add_argument("--document-id", default=None)
    args = parser.parse_args()

    targets = (
        [args.document_id]
        if args.document_id
        else list(IN_SCOPE_DOCUMENT_IDS)
    )

    results = []
    for incent_key in targets:
        try:
            results.append(recrawl_one(incent_key))
        except Exception as exc:  # noqa: BLE001
            results.append(
                {
                    "incent_key": incent_key,
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if all(r.get("status") == "ok" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
