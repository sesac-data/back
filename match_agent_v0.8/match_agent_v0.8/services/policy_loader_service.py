from database.db import (
    SessionLocal
)

from database.crud import (
    get_latest_policy_version
)


# ─────────────────────────────────────
# 최신 policy json 로드
# ─────────────────────────────────────
def load_latest_policy_json(

    incentive_key: str
):

    db = SessionLocal()

    try:

        latest = (
            get_latest_policy_version(

                db,

                incentive_key
            )
        )

        if not latest:

            print(
                f"[POLICY LOAD FAIL] "
                f"{incentive_key}"
            )

            return None

        return latest.policy_json

    finally:

        db.close()