from services.amount_normalizer import (
    normalize_policy_amounts,
    normalize_support_amount
)

from services.calculation_service import (
    calculate_yearly_amount
)


def test_amount_normalizer():

    support, _ = normalize_support_amount({
        "monthly_amount":
            100000,
        "yearly_max_amount":
            900000,
        "max_duration_months":
            12
    })

    assert support[
        "normalized_yearly_amount"
    ] == 900000

    support, _ = normalize_support_amount({
        "monthly_amount":
            100000,
        "yearly_max_amount":
            None,
        "max_duration_months":
            6
    })

    assert support[
        "normalized_yearly_amount"
    ] == 600000

    support, _ = normalize_support_amount(
        {
            "monthly_amount":
                1400000,
            "yearly_max_amount":
                None,
            "max_duration_months":
                None
        },
        "replacement_workshare_support"
    )

    assert support[
        "normalized_duration_months"
    ] == 12

    assert support[
        "normalized_yearly_amount"
    ] == 16800000

    assert calculate_yearly_amount(
        support
    ) == 16800000

    policy = normalize_policy_amounts(
        {
            "policy_name":
                "amount test",
            "support_items":
                [
                    {
                        "support":
                            {
                                "monthly_amount":
                                    200000,
                                "yearly_max_amount":
                                    None,
                                "max_duration_months":
                                    3
                            }
                    }
                ]
        }
    )

    assert policy[
        "support_items"
    ][0]["support"][
        "normalized_yearly_amount"
    ] == 600000


if __name__ == "__main__":

    test_amount_normalizer()

    print(
        "test_amount_normalizer passed"
    )
