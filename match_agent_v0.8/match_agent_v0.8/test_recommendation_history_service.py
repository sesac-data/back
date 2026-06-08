from database.db import (
    SessionLocal
)

from database.crud import (
    get_recommendation_logs
)


# ─────────────────────────────────────
# 추천 히스토리 조회
# ─────────────────────────────────────
def load_recommendation_history(

    limit: int = 20
):

    db = SessionLocal()

    try:

        logs = (
            get_recommendation_logs(
                db,
                limit
            )
        )

        results = []

        for log in logs:

            results.append({

                "id":
                    log.id,

                "total_amount":
                    log.total_amount,

                "created_at":
                    str(log.created_at),

                "recommendation_result":
                    log.recommendation_result
            })

        return results

    finally:

        db.close()