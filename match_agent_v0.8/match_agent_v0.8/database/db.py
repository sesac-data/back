from sqlalchemy import create_engine

from sqlalchemy.orm import (
    sessionmaker,
    declarative_base
)


# ─────────────────────────────────────
# PostgreSQL 연결 정보
# ─────────────────────────────────────
DATABASE_URL = (

    "postgresql+psycopg2://"

    "postgres:dbswocks"

    "@localhost:5432/"

    "incentive_db"
)


# ─────────────────────────────────────
# Engine
# ─────────────────────────────────────
engine = create_engine(

    DATABASE_URL,

    echo=True
)


# ─────────────────────────────────────
# Session
# ─────────────────────────────────────
SessionLocal = sessionmaker(

    autocommit=False,

    autoflush=False,

    bind=engine
)


# ─────────────────────────────────────
# Base
# ─────────────────────────────────────
Base = declarative_base()