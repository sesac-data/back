from sqlalchemy import (

    Column,
    Integer,
    String,
    Text,
    TIMESTAMP,
    ForeignKey
)

from sqlalchemy.dialects.postgresql import (
    JSONB
)

from sqlalchemy.sql import func

from database.db import Base


# ─────────────────────────────────────
# 정책 메타 테이블
# ─────────────────────────────────────
class Incentive(Base):

    __tablename__ = "incentives"

    id = Column(

        Integer,

        primary_key=True,

        index=True
    )

    incentive_key = Column(

        String,

        unique=True,

        nullable=False
    )

    policy_name = Column(
        String
    )

    category = Column(
        String
    )

    source_url = Column(
        Text
    )

    created_at = Column(

        TIMESTAMP,

        server_default=func.now()
    )


# ─────────────────────────────────────
# 정책 버전 테이블
# ─────────────────────────────────────
class PolicyVersion(Base):

    __tablename__ = "policy_versions"

    id = Column(

        Integer,

        primary_key=True,

        index=True
    )

    incentive_id = Column(

        Integer,

        ForeignKey(
            "incentives.id"
        ),

        nullable=False
    )

    version = Column(

        Integer,

        default=1
    )

    policy_json = Column(
        JSONB
    )

    validation_result = Column(
        JSONB
    )

    extraction_model = Column(
        String
    )

    prompt_version = Column(
        String
    )

    created_at = Column(

        TIMESTAMP,

        server_default=func.now()
    )
    
    
    
# ─────────────────────────────────────
# 추천 로그 테이블
# ─────────────────────────────────────
class RecommendationLog(Base):

    __tablename__ = "recommendation_logs"

    id = Column(

        Integer,

        primary_key=True,

        index=True
    )

    company_snapshot = Column(
        JSONB
    )

    employee_snapshot = Column(
        JSONB
    )

    recommendation_result = Column(
        JSONB
    )

    total_amount = Column(
        Integer
    )

    created_at = Column(

        TIMESTAMP,

        server_default=func.now()
    )