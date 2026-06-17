"""Content-aligned semantic scoring of LLM extraction against human gold.

The existing `services.policy_structure_evaluator` matches support_items by
`support_item_id` and conditions by `condition_id`. A live extraction uses
arbitrary ids (SI-001, C-001), so those ids never line up with the gold's
meaningful ids (SI-LEAVE-INFANT, C-INFANT-AGE) and everything would look
"missing". This script first ALIGNS the candidate to the gold by CONTENT
(amount sets, calculation_type, condition field/operator/expected), relabels the
matched candidate ids to the gold ids, and only then runs the existing evaluator.

Tiers already align by (start_month, end_month) inside the evaluator, so they need
no relabeling.

NOTE: the gold files are AI DRAFTS pending human verification, so these scores
measure agreement with a draft answer key, not ground truth. Use them to locate
divergence, not as a final grade.
"""

import argparse
import json
import os
import sys
from copy import deepcopy
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
APP_DIR = ROOT_DIR / "match_agent_v0.8" / "match_agent_v0.8"
GOLD_DIR = ROOT_DIR / "data" / "policy_extraction_real_eval" / "gold"

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from services.policy_structure_evaluator import (  # noqa: E402
    evaluate_policy_structure,
)


def _amounts(item):
    out = []
    if isinstance(item.get("monthly_amount"), (int, float)):
        out.append(item["monthly_amount"])
    for tier in item.get("tiers", []) or []:
        if isinstance(tier.get("monthly_amount"), (int, float)):
            out.append(tier["monthly_amount"])
    for bonus in item.get("bonuses", []) or []:
        out.extend(_amounts(bonus))
    return out


def _item_similarity(gold_item, cand_item):
    gold_amounts = set(_amounts(gold_item))
    cand_amounts = set(_amounts(cand_item))
    if gold_amounts or cand_amounts:
        union = gold_amounts | cand_amounts
        overlap = len(gold_amounts & cand_amounts) / len(union) if union else 0
    else:
        overlap = 0
    type_bonus = 0.25 if gold_item.get("calculation_type") == cand_item.get(
        "calculation_type"
    ) else 0
    return overlap + type_bonus


def _align_conditions(gold_conditions, cand_conditions):
    used = set()
    for gold_condition in gold_conditions or []:
        key = (
            gold_condition.get("field"),
            gold_condition.get("operator"),
            gold_condition.get("expected"),
        )
        for index, cand_condition in enumerate(cand_conditions or []):
            if index in used:
                continue
            cand_key = (
                cand_condition.get("field"),
                cand_condition.get("operator"),
                cand_condition.get("expected"),
            )
            if cand_key == key or cand_key[0] == key[0]:
                cand_condition["condition_id"] = gold_condition["condition_id"]
                used.add(index)
                break


def align_candidate_to_gold(gold, candidate):
    aligned = deepcopy(candidate)
    gold_items = gold.get("support_items", []) or []
    cand_items = aligned.get("support_items", []) or []

    used = set()
    for gold_item in gold_items:
        best_index = None
        best_score = 0.0
        for index, cand_item in enumerate(cand_items):
            if index in used:
                continue
            score = _item_similarity(gold_item, cand_item)
            if score > best_score:
                best_score = score
                best_index = index
        if best_index is not None and best_score > 0:
            used.add(best_index)
            cand_items[best_index]["support_item_id"] = gold_item[
                "support_item_id"
            ]
            _align_conditions(
                gold_item.get("conditions"),
                cand_items[best_index].get("conditions"),
            )
    return aligned


def score_document(gold, candidate_record):
    candidate = candidate_record.get("assembled_candidate") or {}
    aligned = align_candidate_to_gold(gold, candidate)
    result = evaluate_policy_structure(
        candidate_record.get("source_text", "") or "",
        gold,
        aligned,
        gold.get("policy_id"),
    )

    gold_items = gold.get("support_items", []) or []
    cand_items = candidate.get("support_items", []) or []
    matched = sum(
        1
        for item in aligned.get("support_items", [])
        if item.get("support_item_id")
        in {gi.get("support_item_id") for gi in gold_items}
    )
    return {
        "score": result["score"],
        "passed": result["passed"],
        "error_summary": result["error_summary"],
        "gold_items": len(gold_items),
        "candidate_items": len(cand_items),
        "matched_items": matched,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Score extraction output against the gold dataset (content-aligned)."
    )
    parser.add_argument(
        "--output-dir",
        default=str(ROOT_DIR / "output" / "v6_gpt41_preproc"),
        help="Directory holding {case_id}.json extraction records.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    rows = []
    for gold_path in sorted(GOLD_DIR.glob("*.json")):
        case_id = gold_path.stem
        cand_path = output_dir / f"{case_id}.json"
        if not cand_path.exists():
            continue
        gold = json.loads(gold_path.read_text(encoding="utf-8"))
        record = json.loads(cand_path.read_text(encoding="utf-8"))
        rows.append((case_id, score_document(gold, record)))

    print(f"Scoring against gold (DRAFT) using: {output_dir}")
    print("-" * 88)
    print(
        "%-34s %6s  %-9s  %s"
        % ("document", "score", "items g/c/m", "errors")
    )
    print("-" * 88)
    total = 0.0
    for case_id, r in rows:
        errs = ", ".join(
            f"{k}:{v}" for k, v in sorted(r["error_summary"].items())
        ) or "-"
        total += r["score"]
        print(
            "%-34s %6.1f  %d/%d/%d      %s"
            % (
                case_id,
                r["score"],
                r["gold_items"],
                r["candidate_items"],
                r["matched_items"],
                errs,
            )
        )
    print("-" * 88)
    if rows:
        print("average score: %.1f  (vs draft gold; not ground truth)" % (total / len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
