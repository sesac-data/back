from services.condition_coverage_auditor import (
    audit_condition_coverage,
    collect_condition_usage,
)


POLICIES = [
    {
        "policy_key": "POLICY-A",
        "support_items": [
            {
                "conditions": [
                    {"type": "child_age", "max": 8},
                    {"type": "monthly_overtime_hours", "max": 10},
                    {"field": "employee.x", "operator": "gte", "expected": 1},
                    {"field": "employee.y", "operator": "weird_op", "expected": 1},
                ]
            }
        ],
    },
    {
        "policy_key": "POLICY-B",
        "conditions": [
            {"type": "monthly_overtime_hours", "max": 5},
            {"type": "requires_attendance_system", "value": True},
        ],
    },
]


def test_collects_types_and_operators_with_policy_ids():
    usage = collect_condition_usage(POLICIES)
    assert usage["type_counts"]["child_age"] == 1
    assert usage["type_counts"]["monthly_overtime_hours"] == 2
    assert usage["operator_counts"]["gte"] == 1
    assert sorted(usage["type_policies"]["monthly_overtime_hours"]) == [
        "POLICY-A",
        "POLICY-B",
    ]


def test_audit_separates_supported_and_unsupported():
    report = audit_condition_coverage(POLICIES)
    assert report["policy_count"] == 2
    assert "child_age" in report["supported_types"]
    assert "requires_attendance_system" in report["supported_types"]

    unsupported_types = {item["type"] for item in report["unsupported_types"]}
    assert "monthly_overtime_hours" in unsupported_types

    unsupported_ops = {item["operator"] for item in report["unsupported_operators"]}
    assert "weird_op" in unsupported_ops
    assert "gte" in report["supported_operators"]
    assert report["has_gaps"] is True


def test_unsupported_type_carries_count_and_policies():
    report = audit_condition_coverage(POLICIES)
    overtime = next(
        item
        for item in report["unsupported_types"]
        if item["type"] == "monthly_overtime_hours"
    )
    assert overtime["count"] == 2
    assert overtime["policies"] == ["POLICY-A", "POLICY-B"]


def test_no_gaps_when_all_supported():
    report = audit_condition_coverage(
        [{"policy_key": "P", "conditions": [{"type": "child_age", "max": 8}]}]
    )
    assert report["has_gaps"] is False
    assert report["unsupported_types"] == []


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("test_condition_coverage_auditor passed")
