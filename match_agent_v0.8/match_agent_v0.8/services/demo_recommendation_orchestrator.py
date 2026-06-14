from typing import Dict

from services.approved_policy_loader import (
    load_approved_policies,
)
from services.calculation_service import (
    calculate_base_policy_support,
    calculate_conditional_bonus_policy_support,
    get_support_calculation_type,
    normalize_policy_calculation_result,
)
from services.combination_amount_summarizer import (
    summarize_combination_amounts,
)
from services.employer_net_cost_calculator import (
    calculate_employer_net_costs,
)
from services.optimal_combination_selector import (
    select_optimal_combination,
)
from services.policy_combination_generator import (
    generate_valid_policy_combinations,
)
from services.rule_engine_domain_adapter import (
    adapt_general_company_request_to_rule_engine,
)


DEMO_META = {
    "data_source": "demo_fixture",
    "is_demo": True,
}
ALLOWED_POLICY_SOURCES = [
    "demo_fixture",
    "policy_db",
]


def build_error(
    field: str,
    reason: str,
    details=None
) -> Dict:

    return {
        "field":
            field,
        "reason":
            reason,
        "details":
            details,
    }


def get_requested_policy_source(
    payload
) -> str:

    if not isinstance(
        payload,
        dict
    ):

        return "demo_fixture"

    return payload.get(
        "policy_source"
    ) or "demo_fixture"


def build_meta(
    requested_policy_source="demo_fixture",
    policy_source=None,
    loaded_policy_count=0,
    requested_months=None,
    standardized_policy_result_count=None,
) -> Dict:

    policy_source = policy_source or {
        "data_source":
            requested_policy_source,
        "is_demo":
            requested_policy_source == "demo_fixture",
    }

    meta = {
        "data_source":
            policy_source.get(
                "data_source",
                requested_policy_source,
            ),
        "is_demo":
            policy_source.get(
                "is_demo",
                requested_policy_source == "demo_fixture",
            ),
        "policy_source":
            policy_source,
        "loaded_policy_count":
            loaded_policy_count,
    }

    if policy_source.get(
        "fixture"
    ):

        meta["fixture"] = policy_source.get(
            "fixture"
        )

    if requested_months is not None:

        meta["requested_months"] = requested_months

    if standardized_policy_result_count is not None:

        meta["standardized_policy_result_count"] = (
            standardized_policy_result_count
        )

    return meta


def validate_demo_recommendation_request(
    payload
) -> Dict:

    errors = []

    if not isinstance(
        payload,
        dict
    ):

        return {
            "valid":
                False,
            "errors":
                [
                    build_error(
                        "body",
                        "request_body_must_be_object",
                    )
                ],
        }

    for field in [
        "company",
        "employee",
        "leave_event",
    ]:

        if not isinstance(
            payload.get(
                field
            ),
            dict
        ):

            errors.append(
                build_error(
                    field,
                    "object_required",
                )
            )

    employer_cost_items = payload.get(
        "employer_cost_items",
        []
    )

    if employer_cost_items is not None and not isinstance(
        employer_cost_items,
        list
    ):

        errors.append(
            build_error(
                "employer_cost_items",
                "array_required",
            )
        )

    policy_source = get_requested_policy_source(
        payload
    )

    if policy_source not in ALLOWED_POLICY_SOURCES:

        errors.append(
            build_error(
                "policy_source",
                "unsupported_policy_source",
                {
                    "allowed_values":
                        ALLOWED_POLICY_SOURCES,
                    "received":
                        policy_source,
                },
            )
        )

    return {
        "valid":
            not errors,
        "errors":
            errors,
    }


def calculate_policy(
    policy,
    rule_input,
    requested_months
):

    calculation_type = get_support_calculation_type(
        policy
    )

    if calculation_type == "conditional_bonus":

        return calculate_conditional_bonus_policy_support(
            policy,
            rule_input,
            requested_months,
        )

    return calculate_base_policy_support(
        policy,
        rule_input,
        requested_months,
    )


def run_demo_recommendation_pipeline(
    payload: Dict
) -> Dict:

    validation = validate_demo_recommendation_request(
        payload
    )

    if not validation.get(
        "valid"
    ):

        return {
            "recommended_combination":
                None,
            "alternative_combinations":
                [],
            "rejected_combinations":
                [],
            "errors":
                validation.get(
                    "errors",
                    []
                ),
            "meta":
                build_meta(
                    get_requested_policy_source(
                        payload
                    )
                ),
        }

    errors = []
    requested_policy_source = get_requested_policy_source(
        payload
    )
    policy_load_result = load_approved_policies(
        source=requested_policy_source
    )

    if policy_load_result.get(
        "errors"
    ):

        return {
            "recommended_combination":
                None,
            "alternative_combinations":
                [],
            "rejected_combinations":
                [],
            "errors":
                policy_load_result.get(
                    "errors",
                    []
                ),
            "meta":
                build_meta(
                    requested_policy_source,
                    policy_load_result.get(
                        "policy_source",
                        {},
                    ),
                    0,
                ),
        }

    candidate_policies = policy_load_result.get(
        "candidate_policies",
        []
    )
    policy_source = policy_load_result.get(
        "policy_source",
        {}
    )
    employer_cost_items = payload.get(
        "employer_cost_items",
        []
    ) or []

    adapter_result = adapt_general_company_request_to_rule_engine(
        payload
    )

    if adapter_result.get(
        "errors"
    ):
        return {
            "recommended_combination":
                None,
            "alternative_combinations":
                [],
            "rejected_combinations":
                [],
            "errors":
                adapter_result.get(
                    "errors",
                    []
                ),
            "meta":
                build_meta(
                    requested_policy_source,
                    policy_source,
                    len(
                        candidate_policies
                    ),
                ),
        }

    requested_months = adapter_result.get(
        "requested_months"
    )
    rule_input = adapter_result.get(
        "rule_input",
        {}
    )

    standardized_policy_results = []

    for policy in candidate_policies:

        policy_id = (
            policy.get(
                "policy_id"
            )
            or policy.get(
                "policy_key"
            )
        )

        try:

            raw_result = calculate_policy(
                policy,
                rule_input,
                requested_months,
            )
            standardized_policy_results.append(
                normalize_policy_calculation_result(
                    policy,
                    raw_result,
                )
            )

        except Exception as exc:

            errors.append({
                "stage":
                    "policy_calculation",
                "policy_id":
                    policy_id,
                "type":
                    exc.__class__.__name__,
                "message":
                    str(
                        exc
                    ),
            })

    combination_result = generate_valid_policy_combinations(
        candidate_policies
    )
    errors.extend(
        {
            "stage":
                "generate_valid_policy_combinations",
            **error,
        }
        for error in combination_result.get(
            "errors",
            []
        )
    )

    rejected_combinations = [
        {
            "stage":
                "policy_combination_generation",
            **combination,
        }
        for combination in combination_result.get(
            "rejected_combinations",
            []
        )
    ]

    summary_result = summarize_combination_amounts(
        combination_result.get(
            "valid_combinations",
            []
        ),
        standardized_policy_results,
    )
    errors.extend(
        {
            "stage":
                "summarize_combination_amounts",
            **error,
        }
        for error in summary_result.get(
            "errors",
            []
        )
    )
    rejected_combinations.extend(
        {
            "stage":
                "combination_amount_summarization",
            **combination,
        }
        for combination in summary_result.get(
            "rejected_combinations",
            []
        )
    )

    net_cost_result = calculate_employer_net_costs(
        summary_result.get(
            "summarized_combinations",
            []
        ),
        employer_cost_items,
    )
    errors.extend(
        {
            "stage":
                "calculate_employer_net_costs",
            **error,
        }
        for error in net_cost_result.get(
            "errors",
            []
        )
    )

    selection_result = select_optimal_combination(
        net_cost_result.get(
            "cost_calculated_combinations",
            []
        ),
        rejected_combinations,
    )

    errors.extend(
        {
            "stage":
                "select_optimal_combination",
            **error,
        }
        for error in selection_result.get(
            "errors",
            []
        )
    )

    return {
        "recommended_combination":
            selection_result.get(
                "recommended_combination"
            ),
        "alternative_combinations":
            selection_result.get(
                "alternative_combinations",
                []
            ),
        "rejected_combinations":
            selection_result.get(
                "rejected_combinations",
                []
            ),
        "errors":
            errors,
            "meta":
                build_meta(
                    requested_policy_source,
                    policy_source,
                    len(
                        candidate_policies
                    ),
                    requested_months,
                    len(
                        standardized_policy_results
                    ),
                ),
    }
