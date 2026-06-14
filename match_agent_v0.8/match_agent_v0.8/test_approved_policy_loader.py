import os
from contextlib import contextmanager

from services.approved_policy_loader import (
    filter_approved_policies,
    load_approved_policies,
)


@contextmanager
def temporary_env(
    removals=None,
):

    removals = removals or []
    previous_values = {
        name:
            os.environ.get(
                name
            )
        for name in removals
    }

    try:

        for name in removals:

            os.environ.pop(
                name,
                None,
            )

        yield

    finally:

        for name, value in previous_values.items():

            if value is None:

                os.environ.pop(
                    name,
                    None,
                )

            else:

                os.environ[
                    name
                ] = value


class FakeCursor:

    def __init__(
        self,
        rows=None,
        execute_error=None,
    ):

        self.rows = rows or []
        self.execute_error = execute_error

    def __enter__(
        self
    ):

        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ):

        return False

    def execute(
        self,
        query,
    ):

        if self.execute_error:

            raise self.execute_error

        self.query = query

    def fetchall(
        self
    ):

        return [
            row
            for row in self.rows
            if row.get(
                "review_status"
            ) == "approved"
            and row.get(
                "is_active"
            ) is True
        ]


class FakeConnection:

    def __init__(
        self,
        rows=None,
        execute_error=None,
    ):

        self.rows = rows or []
        self.execute_error = execute_error
        self.closed = False

    def __enter__(
        self
    ):

        return self

    def __exit__(
        self,
        exc_type,
        exc,
        traceback,
    ):

        return False

    def cursor(
        self
    ):

        return FakeCursor(
            self.rows,
            self.execute_error,
        )

    def close(
        self
    ):

        self.closed = True


def connection_factory_for(
    rows=None,
    execute_error=None,
):

    def factory(
        db_url
    ):

        if db_url == "raise-connection":

            raise RuntimeError(
                "connection failed"
            )

        return FakeConnection(
            rows,
            execute_error,
        )

    return factory


def approved_row(
    policy_id="approved-policy",
    policy_json=None,
    review_status="approved",
    is_active=True,
):

    return {
        "policy_id":
            policy_id,
        "policy_name":
            "Approved Policy",
        "policy_version":
            "v1",
        "review_status":
            review_status,
        "is_active":
            is_active,
        "policy_json":
            policy_json
            or {
                "policy_id":
                    policy_id,
                "policy_key":
                    policy_id,
                "policy_name":
                    "Approved Policy",
                "review_status":
                    review_status,
                "support_items":
                    [],
            },
    }


def test_demo_fixture_loader_returns_approved_policies():

    result = load_approved_policies()

    assert result["errors"] == []
    assert result["candidate_policies"]
    assert all(
        policy["review_status"] == "approved"
        for policy in result["candidate_policies"]
    )


def test_loader_filters_unapproved_policies():

    policies = [
        {
            "policy_id":
                "approved-policy",
            "review_status":
                "approved",
        },
        {
            "policy_id":
                "review-policy",
            "review_status":
                "needs_review",
        },
        {
            "policy_id":
                "deprecated-policy",
            "review_status":
                "deprecated",
        },
    ]

    approved = filter_approved_policies(
        policies
    )

    assert [
        policy["policy_id"]
        for policy in approved
    ] == [
        "approved-policy"
    ]


def test_loader_returns_deep_copied_policies():

    policies = [
        {
            "policy_id":
                "approved-policy",
            "review_status":
                "approved",
            "support_items":
                [
                    {
                        "support_type":
                            "monthly_fixed",
                    }
                ],
        }
    ]

    approved = filter_approved_policies(
        policies
    )
    approved[0]["support_items"][0]["support_type"] = "changed"

    assert policies[0]["support_items"][0]["support_type"] == "monthly_fixed"


def test_policy_db_loads_approved_active_policies():

    result = load_approved_policies(
        source="policy_db",
        db_url="postgresql://test",
        connection_factory=connection_factory_for(
            [
                approved_row()
            ]
        ),
    )

    assert result["errors"] == []
    assert result["policy_source"]["data_source"] == "policy_db"
    assert result["policy_source"]["table"] == "subsidy_policies"
    assert result["candidate_policies"][0]["policy_id"] == "approved-policy"


def test_policy_db_query_excludes_non_approved_and_inactive_rows():

    result = load_approved_policies(
        source="policy_db",
        db_url="postgresql://test",
        connection_factory=connection_factory_for(
            [
                approved_row(
                    "approved-policy"
                ),
                approved_row(
                    "needs-review-policy",
                    review_status="needs_review",
                ),
                approved_row(
                    "deprecated-policy",
                    review_status="deprecated",
                ),
                approved_row(
                    "inactive-policy",
                    is_active=False,
                ),
            ]
        ),
    )

    assert result["errors"] == []
    assert [
        policy["policy_id"]
        for policy in result["candidate_policies"]
    ] == [
        "approved-policy"
    ]


def test_policy_db_approved_policy_not_found():

    result = load_approved_policies(
        source="policy_db",
        db_url="postgresql://test",
        connection_factory=connection_factory_for(
            []
        ),
    )

    assert result["candidate_policies"] == []
    assert result["errors"][0]["reason"] == "approved_policy_not_found"


def test_policy_db_connection_failed_without_url():

    with temporary_env(
        removals=[
            "INCENTDOC_POLICY_DB_URL",
            "INCENTDOC_RUN_POLICY_DB_INTEGRATION",
        ]
    ):

        result = load_approved_policies(
            source="policy_db",
            db_url="",
            connection_factory=connection_factory_for(
                []
            ),
        )

    assert result["candidate_policies"] == []
    assert result["errors"][0]["reason"] == "policy_db_connection_failed"


def test_policy_db_connection_failed_from_driver():

    result = load_approved_policies(
        source="policy_db",
        db_url="raise-connection",
        connection_factory=connection_factory_for(
            []
        ),
    )

    assert result["candidate_policies"] == []
    assert result["errors"][0]["reason"] == "policy_db_connection_failed"


def test_policy_db_table_not_found():

    result = load_approved_policies(
        source="policy_db",
        db_url="postgresql://test",
        connection_factory=connection_factory_for(
            [],
            RuntimeError(
                'relation "subsidy_policies" does not exist'
            ),
        ),
    )

    assert result["candidate_policies"] == []
    assert result["errors"][0]["reason"] == "policy_db_table_not_found"


def test_policy_db_invalid_json():

    result = load_approved_policies(
        source="policy_db",
        db_url="postgresql://test",
        connection_factory=connection_factory_for(
            [
                approved_row(
                    policy_json="{invalid json"
                )
            ]
        ),
    )

    assert result["candidate_policies"] == []
    assert result["errors"][0]["reason"] == "policy_db_invalid_json"


def test_policy_db_review_status_mismatch():

    result = load_approved_policies(
        source="policy_db",
        db_url="postgresql://test",
        connection_factory=connection_factory_for(
            [
                approved_row(
                    policy_json={
                        "policy_id":
                            "approved-policy",
                        "review_status":
                            "needs_review",
                    }
                )
            ]
        ),
    )

    assert result["candidate_policies"] == []
    assert result["errors"][0]["reason"] == "policy_db_review_status_mismatch"


def test_unknown_source_returns_structured_error():

    result = load_approved_policies(
        source="unknown_source"
    )

    assert result["candidate_policies"] == []
    assert result["policy_source"]["data_source"] == "unknown_source"
    assert result["errors"][0]["reason"] == "unsupported_policy_source"


def test_missing_demo_fixture_returns_structured_error():

    result = load_approved_policies(
        fixture_name="missing_fixture"
    )

    assert result["candidate_policies"] == []
    assert result["policy_source"]["is_demo"] is True
    assert result["errors"][0]["reason"] == "demo_fixture_not_found"


def test_policy_source_marks_demo_fixture_boundary():

    result = load_approved_policies()
    policy_source = result["policy_source"]

    assert policy_source["data_source"] == "demo_fixture"
    assert policy_source["is_demo"] is True
    assert policy_source["fixture"] == "optimal_combination"
    assert "TEST FIXTURE ONLY" in policy_source["fixture_notice"]
    assert policy_source["approved_policy_count"] == len(
        result["candidate_policies"]
    )


def test_optional_real_policy_db_integration():

    if os.getenv(
        "INCENTDOC_RUN_POLICY_DB_INTEGRATION"
    ) != "true":

        print(
            "Skipping real policy_db integration: set INCENTDOC_RUN_POLICY_DB_INTEGRATION=true and INCENTDOC_POLICY_DB_URL."
        )
        return

    result = load_approved_policies(
        source="policy_db"
    )

    assert result["errors"] == []
    assert result["candidate_policies"]


if __name__ == "__main__":

    test_demo_fixture_loader_returns_approved_policies()
    test_loader_filters_unapproved_policies()
    test_loader_returns_deep_copied_policies()
    test_policy_db_loads_approved_active_policies()
    test_policy_db_query_excludes_non_approved_and_inactive_rows()
    test_policy_db_approved_policy_not_found()
    test_policy_db_connection_failed_without_url()
    test_policy_db_connection_failed_from_driver()
    test_policy_db_table_not_found()
    test_policy_db_invalid_json()
    test_policy_db_review_status_mismatch()
    test_unknown_source_returns_structured_error()
    test_missing_demo_fixture_returns_structured_error()
    test_policy_source_marks_demo_fixture_boundary()
    test_optional_real_policy_db_integration()
    print("test_approved_policy_loader passed")
