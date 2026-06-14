from copy import deepcopy
from typing import Any, Dict, List, Tuple


ERROR_TYPES = [
    "missing_field",
    "value_mismatch",
    "type_mismatch",
    "missing_condition",
    "operator_mismatch",
    "amount_mismatch",
    "duration_mismatch",
    "tier_mismatch",
    "missing_evidence",
    "missing_combination_rule",
    "invalid_review_status",
]

AMOUNT_FIELDS = {
    "monthly_amount",
    "yearly_max_amount",
    "normalized_yearly_amount",
    "bonus_amount",
}
DURATION_FIELDS = {
    "max_months",
    "max_duration_months",
    "duration_months",
}


def evaluate_policy_structure(
    source_text: str,
    expected_policy: Dict,
    candidate_policy: Dict,
    policy_id=None,
) -> Dict:

    evaluator = PolicyStructureEvaluator(
        source_text,
        expected_policy,
        candidate_policy,
        policy_id,
    )
    return evaluator.evaluate()


def evaluate_policy_structure_cases(
    cases: List[Dict]
) -> Dict:

    results = []

    for case in cases:

        result = evaluate_policy_structure(
            case.get(
                "source_text",
                "",
            ),
            case.get(
                "expected_policy",
                {},
            ),
            case.get(
                "candidate_policy",
                {},
            ),
            case.get(
                "case_id"
            ),
        )
        result["case_id"] = case.get(
            "case_id"
        )
        result["case_name"] = case.get(
            "case_name"
        )
        results.append(
            result
        )

    passed = all(
        result.get(
            "passed"
        )
        for result in results
    )

    return {
        "passed":
            passed,
        "case_count":
            len(
                results
            ),
        "average_score":
            round(
                sum(
                    result.get(
                        "score",
                        0,
                    )
                    for result in results
                )
                / len(
                    results
                ),
                2,
            )
            if results
            else 0,
        "results":
            results,
    }


def render_markdown_report(
    report: Dict
) -> str:

    lines = [
        "# Policy Extraction Evaluation Report",
        "",
        f"- Overall passed: {report.get('passed')}",
        f"- Case count: {report.get('case_count', 0)}",
        f"- Average score: {report.get('average_score', 0)}",
        "",
        "| Case | Passed | Score | Errors |",
        "| --- | --- | ---: | --- |",
    ]

    for result in report.get(
        "results",
        []
    ):

        errors = ", ".join(
            sorted(
                {
                    error.get(
                        "error_type"
                    )
                    for error in result.get(
                        "errors",
                        []
                    )
                }
            )
        ) or "-"
        lines.append(
            "| {case} | {passed} | {score} | {errors} |".format(
                case=result.get(
                    "case_id"
                ),
                passed=result.get(
                    "passed"
                ),
                score=result.get(
                    "score"
                ),
                errors=errors,
            )
        )

    lines.extend(
        [
            "",
            "## Details",
            "",
        ]
    )

    for result in report.get(
        "results",
        []
    ):

        lines.extend(
            [
                f"### {result.get('case_id')}",
                "",
                f"- Policy ID: `{result.get('policy_id')}`",
                f"- Passed checks: {result.get('passed_checks')} / {result.get('total_checks')}",
                f"- Score: {result.get('score')}",
                "",
            ]
        )

        if not result.get(
            "errors"
        ):

            lines.append(
                "- Errors: none"
            )
            lines.append(
                ""
            )
            continue

        lines.append(
            "| Type | Path | Expected | Actual |"
        )
        lines.append(
            "| --- | --- | --- | --- |"
        )

        for error in result.get(
            "errors",
            []
        ):

            lines.append(
                "| {kind} | `{path}` | `{expected}` | `{actual}` |".format(
                    kind=error.get(
                        "error_type"
                    ),
                    path=error.get(
                        "path"
                    ),
                    expected=_markdown_value(
                        error.get(
                            "expected"
                        )
                    ),
                    actual=_markdown_value(
                        error.get(
                            "actual"
                        )
                    ),
                )
            )

        lines.append(
            ""
        )

    return "\n".join(
        lines
    ) + "\n"


class PolicyStructureEvaluator:

    def __init__(
        self,
        source_text: str,
        expected_policy: Dict,
        candidate_policy: Dict,
        policy_id=None,
    ):

        self.source_text = source_text
        self.expected_policy = expected_policy or {}
        self.candidate_policy = candidate_policy or {}
        self.policy_id = (
            policy_id
            or self.expected_policy.get(
                "policy_id"
            )
            or self.expected_policy.get(
                "policy_key"
            )
        )
        self.errors = []
        self.total_checks = 0
        self.passed_checks = 0

    def evaluate(
        self
    ) -> Dict:

        self._check_review_status()
        self._compare_object(
            self.expected_policy,
            self.candidate_policy,
            "policy",
        )

        score = (
            round(
                self.passed_checks
                / self.total_checks
                * 100,
                2,
            )
            if self.total_checks
            else 0
        )

        return {
            "policy_id":
                self.policy_id,
            "passed":
                not self.errors,
            "score":
                score,
            "passed_checks":
                self.passed_checks,
            "total_checks":
                self.total_checks,
            "errors":
                self.errors,
            "error_summary":
                self._summarize_errors(),
        }

    def _check_review_status(
        self
    ):

        self._check(
            self.candidate_policy.get(
                "review_status"
            )
            == "needs_review",
            "invalid_review_status",
            "policy.review_status",
            "needs_review",
            self.candidate_policy.get(
                "review_status"
            ),
        )

    def _compare_object(
        self,
        expected: Dict,
        actual: Dict,
        path: str,
    ):

        if not isinstance(
            actual,
            dict
        ):

            self._check(
                False,
                "type_mismatch",
                path,
                "object",
                type(
                    actual
                ).__name__,
            )
            return

        for key, expected_value in expected.items():

            next_path = f"{path}.{key}"

            if key not in actual:

                self._check(
                    False,
                    "missing_field",
                    next_path,
                    expected_value,
                    None,
                )
                continue

            self._compare_value(
                key,
                expected_value,
                actual.get(
                    key
                ),
                next_path,
            )

    def _compare_value(
        self,
        key: str,
        expected: Any,
        actual: Any,
        path: str,
    ):

        if key == "review_status":

            return

        if isinstance(
            expected,
            dict
        ):

            self._compare_object(
                expected,
                actual,
                path,
            )
            return

        if isinstance(
            expected,
            list
        ):

            self._compare_list(
                key,
                expected,
                actual,
                path,
            )
            return

        if type(expected) is not type(actual) and expected is not None:

            self._check(
                False,
                "type_mismatch",
                path,
                type(
                    expected
                ).__name__,
                type(
                    actual
                ).__name__,
            )
            return

        error_type = self._scalar_error_type(
            key
        )
        self._check(
            expected == actual,
            error_type,
            path,
            expected,
            actual,
        )

    def _compare_list(
        self,
        key: str,
        expected: List,
        actual: Any,
        path: str,
    ):

        if not isinstance(
            actual,
            list
        ):

            self._check(
                False,
                "type_mismatch",
                path,
                "list",
                type(
                    actual
                ).__name__,
            )
            return

        if key == "conditions":

            self._compare_indexed_list(
                expected,
                actual,
                "condition_id",
                path,
                "missing_condition",
            )
            return

        if key == "tiers":

            self._compare_indexed_list(
                expected,
                actual,
                _tier_key,
                path,
                "tier_mismatch",
            )
            return

        if key == "combination_rules":

            self._compare_indexed_list(
                expected,
                actual,
                "rule_id",
                path,
                "missing_combination_rule",
            )
            return

        if key == "support_items":

            self._compare_indexed_list(
                expected,
                actual,
                "support_item_id",
                path,
                "missing_field",
            )
            return

        if key == "evidence_snippets":

            self._check(
                _sorted_copy(
                    expected
                )
                == _sorted_copy(
                    actual
                ),
                "missing_evidence",
                path,
                expected,
                actual,
            )
            return

        self._check(
            _sorted_copy(
                expected
            )
            == _sorted_copy(
                actual
            ),
            "value_mismatch",
            path,
            expected,
            actual,
        )

    def _compare_indexed_list(
        self,
        expected: List[Dict],
        actual: List[Dict],
        key,
        path: str,
        missing_error_type: str,
    ):

        actual_map = _index_by(
            actual,
            key,
        )

        for expected_item in expected:

            item_key = _item_key(
                expected_item,
                key,
            )
            item_path = f"{path}[{item_key}]"

            if item_key not in actual_map:

                self._check(
                    False,
                    missing_error_type,
                    item_path,
                    expected_item,
                    None,
                )
                continue

            self._compare_object(
                expected_item,
                actual_map[
                    item_key
                ],
                item_path,
            )

    def _scalar_error_type(
        self,
        key: str,
    ) -> str:

        if key == "operator":
            return "operator_mismatch"

        if key in AMOUNT_FIELDS:
            return "amount_mismatch"

        if key in DURATION_FIELDS:
            return "duration_mismatch"

        return "value_mismatch"

    def _check(
        self,
        passed: bool,
        error_type: str,
        path: str,
        expected,
        actual,
    ):

        self.total_checks += 1

        if passed:

            self.passed_checks += 1
            return

        self.errors.append(
            {
                "error_type":
                    error_type,
                "path":
                    path,
                "expected":
                    expected,
                "actual":
                    actual,
            }
        )

    def _summarize_errors(
        self
    ) -> Dict:

        summary = {}

        for error in self.errors:

            error_type = error.get(
                "error_type"
            )
            summary[error_type] = summary.get(
                error_type,
                0,
            ) + 1

        return summary


def _item_key(
    item: Dict,
    key,
):

    if callable(
        key
    ):

        return key(
            item
        )

    return item.get(
        key
    )


def _index_by(
    items: List[Dict],
    key,
) -> Dict:

    result = {}

    for item in items:

        result[
            _item_key(
                item,
                key,
            )
        ] = item

    return result


def _tier_key(
    tier: Dict
) -> Tuple:

    return (
        tier.get(
            "start_month"
        ),
        tier.get(
            "end_month"
        ),
    )


def _sorted_copy(
    value
):

    copied = deepcopy(
        value
    )

    try:

        return sorted(
            copied,
            key=lambda item: repr(
                item
            ),
        )

    except TypeError:

        return copied


def _markdown_value(
    value
) -> str:

    return str(
        value
    ).replace(
        "|",
        "\\|",
    )
