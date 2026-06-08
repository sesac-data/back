from database.db import (
    SessionLocal
)

from database.crud import (

    get_incentive_by_key,

    create_incentive,

    create_policy_version
)


# ─────────────────────────────────────
# policy db 저장
# ─────────────────────────────────────
def save_policy_to_db(

    incentive_key: str,

    policy_json: dict,

    validation_result: dict,

    source_url: str,

    extraction_model: str = "gpt-4.1",

    prompt_version: str = "v1"
):

    db = SessionLocal()

    try:

        # ─────────────────────
        # incentive 조회
        # ─────────────────────
        incentive = (
            get_incentive_by_key(

                db,

                incentive_key
            )
        )

        # ─────────────────────
        # 없으면 생성
        # ─────────────────────
        if not incentive:

            incentive = (
                create_incentive(

                    db,

                    incentive_key,

                    policy_json.get(
                        "policy_name",
                        incentive_key
                    ),

                    source_url
                )
            )

        # ─────────────────────
        # policy version 저장
        # ─────────────────────
        policy_version = (
            create_policy_version(

                db,

                incentive.id,

                policy_json,

                validation_result,

                extraction_model,

                prompt_version
            )
        )

        print(

            f"[DB SAVE SUCCESS] "

            f"{incentive_key} "

            f"v{policy_version.version}"
        )

    finally:

        db.close()