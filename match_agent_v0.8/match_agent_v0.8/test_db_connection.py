from database.db import engine


try:

    connection = engine.connect()

    print(
        "PostgreSQL 연결 성공"
    )

    connection.close()

except Exception as e:

    print(
        f"DB 연결 실패: {e}"
    )