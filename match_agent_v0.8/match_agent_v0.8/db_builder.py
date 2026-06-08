"""
db_builder.py
지원금 DB 구축 모듈

역할:
  - incent_docs/{key}_docs/ 폴더에 파일이 없으면 URL 크롤링 후 저장
  - URL이 'none'이면 크롤링 스킵 (수동 파일 필요)
  - 저장된 파일(PDF / TXT / JSON)을 읽어 텍스트 반환
  - policy json 자동 생성
  - policy validation 수행
  - PostgreSQL DB 저장
"""

import os
import json
import datetime
import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF

from services.policy_extractor import (
    extract_policy_json,
    save_policy_json
)

from services.condition_normalizer import (
    normalize_policy_conditions
)

from services.amount_normalizer import (
    normalize_policy_amounts
)

from services.policy_validator import (
    validate_policy_json,
    print_validation_result,
    has_validation_errors
)

from services.policy_db_service import (
    save_policy_to_db
)

from config import (
    incent_urls,
    incent_docs_dirs,
    CRAWL_TARGET_CSS,
    CRAWL_ENCODING,
)


# ─────────────────────────────────────────────
# BASE DIR
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


# ─────────────────────────────────────────────
# 내부 유틸
# ─────────────────────────────────────────────

def _has_files(folder: str) -> bool:
    """폴더에 파일이 하나라도 있으면 True"""

    if not os.path.isdir(folder):

        return False

    return any(

        f for f in os.listdir(folder)

        if os.path.isfile(
            os.path.join(folder, f)
        )
    )


def _read_pdf(path: str) -> str:
    """PDF → 텍스트 추출"""

    doc = fitz.open(path)

    return "\n".join(

        page.get_text()

        for page in doc
    )


def _read_txt(path: str) -> str:

    with open(
        path,
        encoding=CRAWL_ENCODING
    ) as f:

        return f.read()


def _read_json(path: str) -> str:
    """meta JSON → content 반환"""

    with open(
        path,
        encoding=CRAWL_ENCODING
    ) as f:

        data = json.load(f)

    return data.get(

        "content",

        json.dumps(
            data,
            ensure_ascii=False
        )
    )


# ─────────────────────────────────────────────
# 크롤링 + 저장
# ─────────────────────────────────────────────

def crawl_and_save(incent_key: str) -> bool:
    """
    URL에서 텍스트를 크롤링하여 저장

    저장:
      - raw txt
      - meta json
      - policy json
      - validation result
      - PostgreSQL

    Returns:
        True  → 성공
        False → 실패
    """

    url = incent_urls.get(
        incent_key,
        "none"
    )

    # ─────────────────────────────
    # URL 없음
    # ─────────────────────────────
    if url == "none":

        print(
            f"[db_builder] "
            f"'{incent_key}' "
            f"URL 없음 → 수동 파일 필요"
        )

        return False

    folder = incent_docs_dirs[incent_key]

    os.makedirs(
        folder,
        exist_ok=True
    )

    # ─────────────────────────────
    # 크롤링
    # ─────────────────────────────
    try:

        headers = {

            "User-Agent": (

                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "

                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "

                "Chrome/124.0.0.0 "
                "Safari/537.36"
            )
        }

        resp = requests.get(

            url,

            headers=headers,

            timeout=15
        )

        resp.raise_for_status()

        resp.encoding = (
            CRAWL_ENCODING
        )

        soup = BeautifulSoup(
            resp.text,
            "html.parser"
        )

        target = soup.select_one(
            CRAWL_TARGET_CSS
        )

        text = (

            target.get_text(
                separator="\n",
                strip=True
            )

            if target

            else

            soup.get_text(
                separator="\n",
                strip=True
            )
        )

    except Exception as e:

        print(
            f"[db_builder] "
            f"크롤링 실패 "
            f"({incent_key}): {e}"
        )

        return False

    # ─────────────────────────────
    # 원문 TXT 저장
    # ─────────────────────────────
    raw_path = os.path.join(

        folder,

        f"{incent_key}_raw.txt"
    )

    with open(

        raw_path,

        "w",

        encoding=CRAWL_ENCODING

    ) as f:

        f.write(text)

    # ─────────────────────────────
    # 메타 JSON 저장
    # ─────────────────────────────
    meta = {

        "incent_key":
            incent_key,

        "url":
            url,

        "crawled_at":
            datetime.datetime.now().isoformat(),

        "content":
            text,
    }

    meta_path = os.path.join(

        folder,

        f"{incent_key}_meta.json"
    )

    with open(

        meta_path,

        "w",

        encoding=CRAWL_ENCODING

    ) as f:

        json.dump(

            meta,

            f,

            ensure_ascii=False,

            indent=2
        )

    # ─────────────────────────────
    # policy json 경로
    # ─────────────────────────────
    policy_json_path = os.path.join(

        BASE_DIR,

        "data",

        "policy_json",

        f"{incent_key}.json"
    )

    # ─────────────────────────────
    # policy extraction
    # ─────────────────────────────
    try:

        if os.path.exists(
            policy_json_path
        ):

            print(
                f"[db_builder] "
                f"'{incent_key}' "
                f"policy json 이미 존재 → skip"
            )

            return True

        print(
            f"[db_builder] "
            f"'{incent_key}' "
            f"policy extraction 시작"
        )

        # ─────────────────────────
        # extraction
        # ─────────────────────────
        policy_json = (
            extract_policy_json(
                text
            )
        )

        # ─────────────────────────
        # validation
        # ─────────────────────────
        # Normalize LLM condition aliases before registry validation.
        policy_json = normalize_policy_conditions(
            policy_json
        )

        policy_json = normalize_policy_amounts(
            policy_json,
            incent_key
        )

        normalization_logs = policy_json.get(
            "condition_normalization_logs",
            []
        )

        if normalization_logs:

            print(
                f"[db_builder] "
                f"condition normalized: "
                f"{len(normalization_logs)}"
            )

        validation_result = (
            validate_policy_json(
                policy_json
            )
        )

        print_validation_result(
            validation_result
        )

        # ─────────────────────────
        # json 저장
        # ─────────────────────────
        # Stop invalid policy JSON before local file and DB persistence.
        if has_validation_errors(
            validation_result
        ):

            raise ValueError(
                "policy validation failed"
            )

        save_policy_json(

            incent_key,

            policy_json
        )

        print(
            f"[db_builder] "
            f"'{incent_key}' "
            f"policy json 저장 완료"
        )

        # ─────────────────────────
        # DB 저장
        # ─────────────────────────
        save_policy_to_db(

            incentive_key=incent_key,

            policy_json=policy_json,

            validation_result=validation_result,

            source_url=url,

            extraction_model="gpt-4.1",

            prompt_version="v1"
        )

    except Exception as e:

        print(
            f"[db_builder] "
            f"policy extraction 실패 "
            f"({incent_key}): {e}"
        )

    print(
        f"[db_builder] "
        f"'{incent_key}' "
        f"크롤링 완료 → {raw_path}"
    )

    return True


# ─────────────────────────────────────────────
# DB 텍스트 로드
# ─────────────────────────────────────────────

def load_incent_text(incent_key: str) -> str:
    """
    incent_key 지원금 텍스트 반환
    """

    folder = incent_docs_dirs.get(
        incent_key,
        ""
    )

    # 파일 없으면 크롤링
    if not _has_files(folder):

        crawl_and_save(
            incent_key
        )

    # 그래도 없으면 종료
    if not _has_files(folder):

        print(
            f"[db_builder] "
            f"'{incent_key}' "
            f"DB 파일 없음"
        )

        return ""

    texts = []

    for fname in sorted(
        os.listdir(folder)
    ):

        fpath = os.path.join(
            folder,
            fname
        )

        if not os.path.isfile(
            fpath
        ):

            continue

        ext = fname.lower().rsplit(
            ".",
            1
        )[-1]

        try:

            if ext == "pdf":

                texts.append(
                    _read_pdf(fpath)
                )

            elif ext == "txt":

                texts.append(
                    _read_txt(fpath)
                )

            elif ext == "json":

                texts.append(
                    _read_json(fpath)
                )

        except Exception as e:

            print(
                f"[db_builder] "
                f"파일 읽기 오류 "
                f"({fpath}): {e}"
            )

    return "\n\n".join(texts)


# ─────────────────────────────────────────────
# 전체 지원금 텍스트 로드
# ─────────────────────────────────────────────

def load_all_incent_texts() -> dict[str, str]:

    return {

        key: load_incent_text(key)

        for key in incent_urls
    }


# ─────────────────────────────────────────────
# 앱 시작 시 DB 보장
# ─────────────────────────────────────────────

def ensure_db() -> None:
    """
    앱 시작 시 호출

    빈 폴더면 자동 크롤링
    """

    for key, folder in incent_docs_dirs.items():

        os.makedirs(
            folder,
            exist_ok=True
        )

        crawl_and_save(key)
