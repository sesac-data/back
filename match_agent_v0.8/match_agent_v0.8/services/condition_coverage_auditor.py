"""Audit policy JSON condition types against code-supported condition handling.

The legacy rule engine (`evaluate_condition`) only handles a fixed set of
type-based condition types, and the operator evaluator only a fixed set of
operators. Policy JSON files can contain condition types/operators the code does
not handle, which then fail silently (treated as not-met) instead of being
flagged. This auditor walks policy JSON, collects every condition type and
operator used, and reports which are supported vs unsupported.

It is read-only: it never changes policy JSON, evaluation, or recommendation
behavior.
"""

from typing import Any, Dict, List

from services.condition_evaluator import (
    SUPPORTED_CONDITION_TYPES,
    SUPPORTED_OPERATORS,
)


def _looks_like_type_condition(node: Dict[str, Any]) -> bool:
    return "type" in node and any(
        key in node for key in ("min", "max", "value", "unit")
    )


def _looks_like_operator_condition(node: Dict[str, Any]) -> bool:
    return "operator" in node and "field" in node


def collect_condition_usage(policies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Collect type/operator usage across a list of policy JSON objects.

    Returns counts and, for each usage, the set of policy ids that used it.
    """

    type_counts: Dict[str, int] = {}
    operator_counts: Dict[str, int] = {}
    type_policies: Dict[str, set] = {}
    operator_policies: Dict[str, set] = {}

    def walk(node: Any, policy_id: str) -> None:
        if isinstance(node, dict):
            if _looks_like_type_condition(node):
                ctype = node.get("type")
                type_counts[ctype] = type_counts.get(ctype, 0) + 1
                type_policies.setdefault(ctype, set()).add(policy_id)
            if _looks_like_operator_condition(node):
                operator = node.get("operator")
                operator_counts[operator] = operator_counts.get(operator, 0) + 1
                operator_policies.setdefault(operator, set()).add(policy_id)
            for value in node.values():
                walk(value, policy_id)
        elif isinstance(node, list):
            for item in node:
                walk(item, policy_id)

    for policy in policies:
        policy_id = (
            policy.get("policy_key")
            or policy.get("policy_id")
            or policy.get("policy_name")
            or "UNKNOWN"
        )
        walk(policy, policy_id)

    return {
        "type_counts": type_counts,
        "operator_counts": operator_counts,
        "type_policies": {k: sorted(v) for k, v in type_policies.items()},
        "operator_policies": {k: sorted(v) for k, v in operator_policies.items()},
    }


def audit_condition_coverage(policies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare collected condition usage against code-supported sets."""

    usage = collect_condition_usage(policies)

    supported_types = sorted(
        t for t in usage["type_counts"] if t in SUPPORTED_CONDITION_TYPES
    )
    unsupported_types = sorted(
        t for t in usage["type_counts"] if t not in SUPPORTED_CONDITION_TYPES
    )
    supported_operators = sorted(
        o for o in usage["operator_counts"] if o in SUPPORTED_OPERATORS
    )
    unsupported_operators = sorted(
        o for o in usage["operator_counts"] if o not in SUPPORTED_OPERATORS
    )

    return {
        "policy_count": len(policies),
        "supported_types": supported_types,
        "unsupported_types": [
            {
                "type": t,
                "count": usage["type_counts"][t],
                "policies": usage["type_policies"].get(t, []),
            }
            for t in unsupported_types
        ],
        "supported_operators": supported_operators,
        "unsupported_operators": [
            {
                "operator": o,
                "count": usage["operator_counts"][o],
                "policies": usage["operator_policies"].get(o, []),
            }
            for o in unsupported_operators
        ],
        "has_gaps": bool(unsupported_types or unsupported_operators),
    }
