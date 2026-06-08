from database.db import (
    SessionLocal
)

from database.crud import (
    create_recommendation_log
)


# ─────────────────────────────────────
# 추천 결과 저장
# ─────────────────────────────────────
def save_recommendation_result(

    company_data: dict,

    employee_data: list,

    recommendation_result: dict
):

    db = SessionLocal()

    try:

        total_amount = (
            recommendation_result.get(
                "total_expected_amount",
                0
            )
        )

        log = (
            create_recommendation_log(

                db,

                company_data,

                employee_data,

                recommendation_result,

                total_amount
            )
        )

        print(

            f"[RECOMMENDATION SAVED] "

            f"id={log.id}"
        )

    finally:

        db.close()