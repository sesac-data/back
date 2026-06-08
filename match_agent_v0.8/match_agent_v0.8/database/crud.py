from sqlalchemy.orm import Session

from database.models import (

    Incentive,
    PolicyVersion
)


# ─────────────────────────────────────
# incentive 조회
# ─────────────────────────────────────
def get_incentive_by_key(

    db: Session,

    incentive_key: str
):

    return (

        db.query(Incentive)

        .filter(
            Incentive.incentive_key
            == incentive_key
        )

        .first()
    )


# ─────────────────────────────────────
# incentive 생성
# ─────────────────────────────────────
def create_incentive(

    db: Session,

    incentive_key: str,

    policy_name: str,

    source_url: str
):

    incentive = Incentive(

        incentive_key=incentive_key,

        policy_name=policy_name,

        source_url=source_url
    )

    db.add(incentive)

    db.commit()

    db.refresh(incentive)

    return incentive


# ─────────────────────────────────────
# policy version 저장
# ─────────────────────────────────────
def create_policy_version(

    db: Session,

    incentive_id: int,

    policy_json: dict,

    validation_result: dict,

    extraction_model: str,

    prompt_version: str
):

    # 최신 버전 조회
    latest = (

        db.query(PolicyVersion)

        .filter(
            PolicyVersion.incentive_id
            == incentive_id
        )

        .order_by(
            PolicyVersion.version.desc()
        )

        .first()
    )

    next_version = 1

    if latest:

        next_version = (
            latest.version + 1
        )

    policy_version = PolicyVersion(

        incentive_id=incentive_id,

        version=next_version,

        policy_json=policy_json,

        validation_result=validation_result,

        extraction_model=extraction_model,

        prompt_version=prompt_version
    )

    db.add(policy_version)

    db.commit()

    db.refresh(policy_version)

    return policy_version


# ─────────────────────────────────────
# 최신 policy version 조회
# ─────────────────────────────────────
def get_latest_policy_version(

    db: Session,

    incentive_key: str
):

    incentive = (

        db.query(Incentive)

        .filter(
            Incentive.incentive_key
            == incentive_key
        )

        .first()
    )

    if not incentive:

        return None

    latest = (

        db.query(PolicyVersion)

        .filter(
            PolicyVersion.incentive_id
            == incentive.id
        )

        .order_by(
            PolicyVersion.version.desc()
        )

        .first()
    )

    return latest



# ─────────────────────────────────────
# recommendation 저장
# ─────────────────────────────────────

from database.models import (
    RecommendationLog
)


def create_recommendation_log(

    db: Session,

    company_snapshot: dict,

    employee_snapshot: dict,

    recommendation_result: dict,

    total_amount: int
):

    log = RecommendationLog(

        company_snapshot=company_snapshot,

        employee_snapshot=employee_snapshot,

        recommendation_result=recommendation_result,

        total_amount=total_amount
    )

    db.add(log)

    db.commit()

    db.refresh(log)

    return log


# ─────────────────────────────────────
# 추천 로그 조회
# ─────────────────────────────────────
def get_recommendation_logs(

    db: Session,

    limit: int = 20
):

    return (

        db.query(
            RecommendationLog
        )

        .order_by(
            RecommendationLog.created_at.desc()
        )

        .limit(limit)

        .all()
    )