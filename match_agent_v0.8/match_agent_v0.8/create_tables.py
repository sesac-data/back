from database.db import (
    engine
)

from database.models import (
    Base
)


# ─────────────────────────────────────
# 테이블 생성
# ─────────────────────────────────────
Base.metadata.create_all(
    bind=engine
)

print(
    "테이블 생성 완료"
)