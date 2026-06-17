from services.condition_evaluator import (
    evaluate_condition_group,
    evaluate_conditions_with_groups,
    evaluate_operator_conditions,
    is_condition_group,
)


def _child_age_or_grade_group():
    # 만 12세 이하 또는 초등학교 6학년 이하 (OR)
    return {
        "condition_group_id": "CG-001",
        "mode": "or",
        "conditions": [
            {
                "condition_id": "C-AGE",
                "field": "employee.child_age",
                "operator": "lte",
                "expected": 12,
                "evidence_snippets": ["만 12세 이하"],
            },
            {
                "condition_id": "C-GRADE",
                "field": "employee.child_school_grade",
                "operator": "lte",
                "expected": 6,
                "evidence_snippets": ["초등학교 6학년 이하"],
            },
        ],
        "evidence_snippets": ["만 12세 이하 또는 초등학교 6학년 이하"],
    }


def test_is_condition_group_detects_groups_and_plain_conditions():
    assert is_condition_group(_child_age_or_grade_group()) is True
    assert (
        is_condition_group(
            {"condition_id": "C-1", "field": "a.b", "operator": "eq", "expected": 1}
        )
        is False
    )


def test_or_group_passes_when_any_member_passes():
    group = _child_age_or_grade_group()
    # child_age missing/over 12, but grade <= 6 -> OR passes
    result = evaluate_condition_group(
        {"employee": {"child_age": 14, "child_school_grade": 5}},
        group,
    )
    assert result["passed"] is True
    assert result["reason"] == "passed"
    assert result["mode"] == "or"


def test_or_group_fails_when_no_member_passes():
    group = _child_age_or_grade_group()
    result = evaluate_condition_group(
        {"employee": {"child_age": 14, "child_school_grade": 8}},
        group,
    )
    assert result["passed"] is False
    assert result["reason"] == "group_not_met"


def test_or_group_passes_with_missing_field_on_one_branch():
    group = _child_age_or_grade_group()
    # child_school_grade missing, but child_age <= 12 -> OR still passes
    result = evaluate_condition_group(
        {"employee": {"child_age": 10}},
        group,
    )
    assert result["passed"] is True
    # the missing branch is recorded in member_results
    reasons = {m["reason"] for m in result["member_results"]}
    assert "passed" in reasons
    assert "input_field_missing" in reasons


def test_and_group_requires_all_members():
    group = {
        "condition_group_id": "CG-AND",
        "mode": "and",
        "conditions": [
            {"condition_id": "C-1", "field": "employee.a", "operator": "gte", "expected": 1, "evidence_snippets": ["x"]},
            {"condition_id": "C-2", "field": "employee.b", "operator": "gte", "expected": 1, "evidence_snippets": ["y"]},
        ],
    }
    assert evaluate_condition_group({"employee": {"a": 2, "b": 2}}, group)["passed"] is True
    assert evaluate_condition_group({"employee": {"a": 2, "b": 0}}, group)["passed"] is False


def test_unsupported_group_mode_does_not_pass():
    group = {
        "condition_group_id": "CG-X",
        "mode": "xor",
        "conditions": [
            {"condition_id": "C-1", "field": "employee.a", "operator": "gte", "expected": 1, "evidence_snippets": ["x"]},
        ],
    }
    result = evaluate_condition_group({"employee": {"a": 5}}, group)
    assert result["passed"] is False
    assert result["reason"] == "unsupported_group_mode"


def test_empty_group_does_not_pass():
    group = {"condition_group_id": "CG-E", "mode": "or", "conditions": []}
    result = evaluate_condition_group({}, group)
    assert result["passed"] is False
    assert result["reason"] == "empty_condition_group"


def test_mixed_flat_and_group_aggregation():
    conditions = [
        {"condition_id": "C-HOURS", "field": "employee.weekly_work_hours_before", "operator": "gte", "expected": 35, "evidence_snippets": ["주 35시간 이상"]},
        _child_age_or_grade_group(),
    ]
    # flat passes AND or-group passes -> eligible
    ok = evaluate_conditions_with_groups(
        {"employee": {"weekly_work_hours_before": 40, "child_age": 10}},
        conditions,
    )
    assert ok["eligible"] is True
    assert len(ok["passed_conditions"]) == 1
    assert len(ok["groups"]) == 1

    # flat fails -> ineligible even though group passes
    ng = evaluate_conditions_with_groups(
        {"employee": {"weekly_work_hours_before": 20, "child_age": 10}},
        conditions,
    )
    assert ng["eligible"] is False
    assert len(ng["failed_conditions"]) == 1


def test_no_groups_matches_flat_evaluator():
    conditions = [
        {"condition_id": "C-1", "field": "employee.a", "operator": "gte", "expected": 1, "evidence_snippets": ["x"]},
        {"condition_id": "C-2", "field": "employee.b", "operator": "lte", "expected": 5, "evidence_snippets": ["y"]},
    ]
    data = {"employee": {"a": 2, "b": 3}}
    grouped = evaluate_conditions_with_groups(data, conditions)
    flat = evaluate_operator_conditions(data, conditions)
    assert grouped["eligible"] == flat["eligible"]
    assert len(grouped["passed_conditions"]) == len(flat["passed_conditions"])
    assert grouped["groups"] == []


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("test_condition_group_evaluator passed")
