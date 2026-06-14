import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Dict, List


ROOT_DIR = Path(__file__).resolve().parents[3]
ACCEPTANCE_SCENARIO_DIR = ROOT_DIR / "data" / "acceptance_scenarios"
DEFAULT_POLICY_SOURCE = "demo_fixture"
POLICY_DB_SOURCE = "policy_db"
DEFAULT_FIXTURE_NAME = "optimal_combination"
APPROVED_REVIEW_STATUS = "approved"
POLICY_DB_URL_ENV = "INCENTDOC_POLICY_DB_URL"


def build_policy_loader_error(
    field: str,
    reason: str,
    details=None,
) -> Dict:

    return {
        "field":
            field,
        "reason":
            reason,
        "details":
            details,
    }


def normalize_fixture_name(
    fixture_name
) -> str:

    if not fixture_name:

        return DEFAULT_FIXTURE_NAME

    return str(
        fixture_name
    )


def get_demo_fixture_path(
    fixture_name=DEFAULT_FIXTURE_NAME
) -> Path:

    normalized_name = normalize_fixture_name(
        fixture_name
    )

    return ACCEPTANCE_SCENARIO_DIR / f"{normalized_name}.json"


def load_demo_fixture(
    fixture_name=DEFAULT_FIXTURE_NAME
) -> Dict:

    fixture_path = get_demo_fixture_path(
        fixture_name
    )

    if not fixture_path.exists():

        return {
            "fixture":
                None,
            "path":
                str(
                    fixture_path
                ),
            "errors":
                [
                    build_policy_loader_error(
                        "fixture_name",
                        "demo_fixture_not_found",
                        {
                            "fixture_name":
                                normalize_fixture_name(
                                    fixture_name
                                ),
                            "path":
                                str(
                                    fixture_path
                                ),
                        },
                    )
                ],
        }

    try:

        with fixture_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            fixture = json.load(
                file
            )

    except json.JSONDecodeError as exc:

        return {
            "fixture":
                None,
            "path":
                str(
                    fixture_path
                ),
            "errors":
                [
                    build_policy_loader_error(
                        "fixture",
                        "demo_fixture_invalid_json",
                        {
                            "message":
                                str(
                                    exc
                                ),
                            "path":
                                str(
                                    fixture_path
                                ),
                        },
                    )
                ],
        }

    return {
        "fixture":
            fixture,
        "path":
            str(
                fixture_path
            ),
        "errors":
            [],
    }


def filter_approved_policies(
    candidate_policies: List[Dict]
) -> List[Dict]:

    return [
        deepcopy(
            policy
        )
        for policy in candidate_policies
        if policy.get(
            "review_status"
        ) == APPROVED_REVIEW_STATUS
    ]


def normalize_postgres_url(
    db_url
) -> str:

    if not db_url:

        return ""

    return str(
        db_url
    ).replace(
        "postgresql+psycopg2://",
        "postgresql://",
        1,
    )


def get_policy_db_url(
    db_url=None
) -> str:

    return normalize_postgres_url(
        db_url
        or os.getenv(
            POLICY_DB_URL_ENV
        )
    )


def parse_policy_json(
    value,
    policy_id
) -> Dict:

    if isinstance(
        value,
        dict
    ):

        return {
            "policy_json":
                deepcopy(
                    value
                ),
            "errors":
                [],
        }

    if isinstance(
        value,
        str
    ):

        try:

            parsed = json.loads(
                value
            )

        except json.JSONDecodeError as exc:

            return {
                "policy_json":
                    None,
                "errors":
                    [
                        build_policy_loader_error(
                            "policy_json",
                            "policy_db_invalid_json",
                            {
                                "policy_id":
                                    policy_id,
                                "message":
                                    str(
                                        exc
                                    ),
                            },
                        )
                    ],
            }

        if isinstance(
            parsed,
            dict
        ):

            return {
                "policy_json":
                    parsed,
                "errors":
                    [],
            }

    return {
        "policy_json":
            None,
        "errors":
            [
                build_policy_loader_error(
                    "policy_json",
                    "policy_db_invalid_json",
                    {
                        "policy_id":
                            policy_id,
                        "message":
                            "policy_json must be a JSON object.",
                    },
                )
            ],
    }


def row_get(
    row,
    key
):

    if isinstance(
        row,
        dict
    ):

        return row.get(
            key
        )

    return getattr(
        row,
        key
    )


def default_policy_db_connection_factory(
    db_url
):

    try:

        import psycopg2
        from psycopg2.extras import RealDictCursor

    except ImportError as exc:

        raise RuntimeError(
            "psycopg2 is required for policy_db loading."
        ) from exc

    return psycopg2.connect(
        db_url,
        cursor_factory=RealDictCursor,
    )


def fetch_policy_db_rows(
    db_url,
    connection_factory=None
) -> Dict:

    normalized_url = get_policy_db_url(
        db_url
    )

    if not normalized_url:

        return {
            "rows":
                [],
            "errors":
                [
                    build_policy_loader_error(
                        "database_url",
                        "policy_db_connection_failed",
                        {
                            "env_var":
                                POLICY_DB_URL_ENV,
                            "message":
                                "Policy DB URL is not configured.",
                        },
                    )
                ],
        }

    factory = (
        connection_factory
        or default_policy_db_connection_factory
    )

    try:

        connection = factory(
            normalized_url
        )

    except Exception as exc:

        return {
            "rows":
                [],
            "errors":
                [
                    build_policy_loader_error(
                        "database",
                        "policy_db_connection_failed",
                        {
                            "message":
                                str(
                                    exc
                                ),
                        },
                    )
                ],
        }

    try:

        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        policy_id,
                        policy_name,
                        policy_version,
                        review_status,
                        is_active,
                        policy_json
                    FROM subsidy_policies
                    WHERE review_status = 'approved'
                      AND is_active = TRUE
                    ORDER BY policy_id, policy_version
                    """
                )
                rows = cursor.fetchall()

    except Exception as exc:

        message = str(
            exc
        )
        reason = "policy_db_connection_failed"

        if (
            "subsidy_policies" in message
            and (
                "does not exist" in message
                or "UndefinedTable" in exc.__class__.__name__
            )
        ):

            reason = "policy_db_table_not_found"

        return {
            "rows":
                [],
            "errors":
                [
                    build_policy_loader_error(
                        "subsidy_policies",
                        reason,
                        {
                            "message":
                                message,
                        },
                    )
                ],
        }

    finally:

        close = getattr(
            connection,
            "close",
            None,
        )

        if close:

            close()

    return {
        "rows":
            rows,
        "errors":
            [],
    }


def load_policy_db_approved_policies(
    db_url=None,
    connection_factory=None,
) -> Dict:

    row_result = fetch_policy_db_rows(
        db_url,
        connection_factory,
    )

    policy_source = {
        "data_source":
            POLICY_DB_SOURCE,
        "is_demo":
            False,
        "fixture":
            None,
        "table":
            "subsidy_policies",
        "review_status":
            APPROVED_REVIEW_STATUS,
        "is_active":
            True,
    }

    if row_result.get(
        "errors"
    ):

        return {
            "candidate_policies":
                [],
            "policy_source":
                policy_source,
            "errors":
                row_result.get(
                    "errors",
                    []
                ),
        }

    rows = row_result.get(
        "rows",
        []
    )

    if not rows:

        return {
            "candidate_policies":
                [],
            "policy_source":
                {
                    **policy_source,
                    "approved_policy_count":
                        0,
                },
            "errors":
                [
                    build_policy_loader_error(
                        "subsidy_policies",
                        "approved_policy_not_found",
                        {
                            "review_status":
                                APPROVED_REVIEW_STATUS,
                            "is_active":
                                True,
                        },
                    )
                ],
        }

    policies = []
    errors = []

    for row in rows:

        policy_id = row_get(
            row,
            "policy_id"
        )
        db_review_status = row_get(
            row,
            "review_status"
        )
        parsed = parse_policy_json(
            row_get(
                row,
                "policy_json"
            ),
            policy_id,
        )

        if parsed.get(
            "errors"
        ):

            errors.extend(
                parsed.get(
                    "errors",
                    []
                )
            )
            continue

        policy_json = parsed.get(
            "policy_json"
        )
        json_review_status = policy_json.get(
            "review_status"
        )

        if json_review_status != db_review_status:

            errors.append(
                build_policy_loader_error(
                    "review_status",
                    "policy_db_review_status_mismatch",
                    {
                        "policy_id":
                            policy_id,
                        "db_review_status":
                            db_review_status,
                        "json_review_status":
                            json_review_status,
                    },
                )
            )
            continue

        policies.append(
            policy_json
        )

    if errors:

        return {
            "candidate_policies":
                [],
            "policy_source":
                {
                    **policy_source,
                    "approved_policy_count":
                        len(
                            policies
                        ),
                    "row_count":
                        len(
                            rows
                        ),
                },
            "errors":
                errors,
        }

    return {
        "candidate_policies":
            policies,
        "policy_source":
            {
                **policy_source,
                "approved_policy_count":
                    len(
                        policies
                    ),
                "row_count":
                    len(
                        rows
                    ),
            },
        "errors":
            [],
    }


def load_approved_policies(
    source=DEFAULT_POLICY_SOURCE,
    fixture_name=DEFAULT_FIXTURE_NAME,
    db_url=None,
    connection_factory=None,
) -> Dict:

    if source == POLICY_DB_SOURCE:

        return load_policy_db_approved_policies(
            db_url,
            connection_factory,
        )

    if source != DEFAULT_POLICY_SOURCE:

        return {
            "candidate_policies":
                [],
            "policy_source":
                {
                    "data_source":
                        source,
                    "is_demo":
                        False,
                    "fixture":
                        None,
                },
            "errors":
                [
                    build_policy_loader_error(
                        "source",
                        "unsupported_policy_source",
                        {
                            "source":
                                source,
                            "supported_sources":
                                [
                                    DEFAULT_POLICY_SOURCE,
                                    POLICY_DB_SOURCE,
                                ],
                        },
                    )
                ],
        }

    fixture_result = load_demo_fixture(
        fixture_name
    )

    if fixture_result.get(
        "errors"
    ):

        return {
            "candidate_policies":
                [],
            "policy_source":
                {
                    "data_source":
                        DEFAULT_POLICY_SOURCE,
                    "is_demo":
                        True,
                    "fixture":
                        normalize_fixture_name(
                            fixture_name
                        ),
                    "path":
                        fixture_result.get(
                            "path"
                        ),
                },
            "errors":
                fixture_result.get(
                    "errors",
                    []
                ),
        }

    fixture = fixture_result.get(
        "fixture",
        {}
    )
    all_candidate_policies = fixture.get(
        "candidate_policies",
        []
    )
    approved_policies = filter_approved_policies(
        all_candidate_policies
    )

    return {
        "candidate_policies":
            approved_policies,
        "policy_source":
            {
                "data_source":
                    DEFAULT_POLICY_SOURCE,
                "is_demo":
                    True,
                "fixture":
                    normalize_fixture_name(
                        fixture_name
                    ),
                "path":
                    fixture_result.get(
                        "path"
                    ),
                "fixture_notice":
                    fixture.get(
                        "fixture_notice"
                    ),
                "candidate_policy_count":
                    len(
                        all_candidate_policies
                    ),
                "approved_policy_count":
                    len(
                        approved_policies
                    ),
            },
        "errors":
            [],
    }
