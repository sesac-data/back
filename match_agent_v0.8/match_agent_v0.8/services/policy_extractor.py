# services/policy_extractor.py

import os
import json
import time

from dotenv import load_dotenv
from openai import OpenAI

from services.amount_normalizer import (
    normalize_policy_amounts
)

from services.condition_normalizer import (
    normalize_policy_conditions
)


# ─────────────────────────────────────
# 환경 변수 로드
# ─────────────────────────────────────
load_dotenv()

client = OpenAI()


# ─────────────────────────────────────
# 경로 설정
# ─────────────────────────────────────
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

POLICY_JSON_DIR = os.path.join(
    BASE_DIR,
    "data",
    "policy_json"
)


# ─────────────────────────────────────
# Prompt 생성
# ─────────────────────────────────────
def build_extraction_prompt(
    raw_text: str
) -> str:

    prompt = f"""
당신은 고용노동부 지원금 정책 구조화 전문가입니다.

아래 정책 원문을 읽고,
반드시 지정된 JSON schema 형태로만 변환하세요.

설명 문장 없이 JSON만 반환하세요.

매우 중요:
- 정책별 세부 조건은 conditions 배열로 구조화
- 조건은 계산 가능한 rule 형태로 변환
- 없는 값은 절대 추론하지 말 것
- support item마다 반드시 원문 근거 문장을 evidence_snippets에 저장
- evidence_snippets는 정책 원문의 실제 문장만 사용
- 요약하거나 재작성하지 말 것
- 최대 3개까지만 저장
- 숫자는 숫자형으로 변환
- 금액은 원 단위 숫자로 변환
- 비율은 float로 변환
- 가능한 범용 구조 유지

- condition type은 반드시 아래 목록 중 하나만 사용

허용 condition type:
- child_age
- employee_count
- company_size
- weekly_work_hours
- weekly_working_days
- requires_attendance_system
- requires_groupware
- requires_remote_work_system
- requires_contract_change
- requires_labor_agreement
- requires_replacement_worker
- working_hour_reduction
- new_hire_increase

위 목록에 없는 새로운 condition type 생성 금지

- 사업계획서 제출, 승인 필요 등의 행정 절차는
condition이 아니라
required_documents 또는 application_process로 분류

- target_conditions는 설명용 문자열만 사용
- 실제 계산 조건은 반드시 conditions 배열에만 저장

JSON schema:

{{
  "policy_name": "",

  "policy_category": "",

  "support_items": [

    {{
      "support_type": "",

      "target_conditions": [],

      "conditions": [

        {{
          "type": "",
          "value": null,
          "min": null,
          "max": null
        }}
      ],

      "support": {{

        "monthly_amount": null,

        "yearly_max_amount": null,

        "max_duration_months": null
      }},

      "required_systems": [],

      "required_documents": [],

      "duplicate_allowed": [],

      "important_conditions": [],
      
      "evidence_snippets": []
    }}
  ],

  "support_limit": {{

    "max_people_ratio": null,

    "max_people_limit": null
  }},

  "application_process": [],

  "risk_conditions": []
}}

조건 type 예시:

- child_age
- weekly_work_hours
- requires_attendance_system
- requires_labor_agreement
- requires_contract_change
- requires_replacement_worker
- flexible_work_usage_days
- working_hour_reduction
- weekly_working_days

정책 원문:

{raw_text}
"""

    return prompt


# ─────────────────────────────────────
# 토큰 사용량 출력
# ─────────────────────────────────────
def print_token_usage(response):

    usage = response.usage

    if not usage:

        return

    print("\n==============================")
    print("LLM TOKEN USAGE")
    print("==============================")

    print(
        f"Prompt Tokens     : "
        f"{usage.prompt_tokens}"
    )

    print(
        f"Completion Tokens : "
        f"{usage.completion_tokens}"
    )

    print(
        f"Total Tokens      : "
        f"{usage.total_tokens}"
    )

    print("==============================\n")


# ─────────────────────────────────────
# 정책 구조화
# ─────────────────────────────────────
def extract_policy_json(
    raw_text: str
) -> dict:

    prompt = build_extraction_prompt(
        raw_text
    )

    start_time = time.time()

    response = client.chat.completions.create(

        model="gpt-4.1",

        response_format={
            "type": "json_object"
        },

        messages=[

            {
                "role": "system",

                "content": (
                    "당신은 정책 구조화 전문가입니다."
                )
            },

            {
                "role": "user",

                "content": prompt
            }
        ],

        temperature=0
    )

    end_time = time.time()

    # ─────────────────────────────
    # 토큰 사용량 출력
    # ─────────────────────────────
    print_token_usage(response)

    print(
        f"LLM Response Time : "
        f"{round(end_time - start_time, 2)} sec"
    )

    content = (
        response
        .choices[0]
        .message
        .content
    )

    return json.loads(content)


# ─────────────────────────────────────
# JSON 저장
# ─────────────────────────────────────
def save_policy_json(
    policy_key: str,
    policy_json: dict
):

    os.makedirs(
        POLICY_JSON_DIR,
        exist_ok=True
    )

    file_path = os.path.join(
        POLICY_JSON_DIR,
        f"{policy_key}.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            policy_json,
            f,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"\nPolicy JSON Saved:"
        f"\n{file_path}\n"
    )

    return file_path


# ─────────────────────────────────────
# JSON 로드
# ─────────────────────────────────────
def load_policy_json(
    policy_key: str
) -> dict:

    file_path = os.path.join(
        POLICY_JSON_DIR,
        f"{policy_key}.json"
    )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        policy_json = json.load(f)

    policy_json = normalize_policy_conditions(
        policy_json
    )

    return normalize_policy_amounts(
        policy_json,
        policy_key
    )


# ─────────────────────────────────────
# 실행 테스트
# ─────────────────────────────────────
if __name__ == "__main__":

    from db_builder import load_incent_text

    policy_key = (
        "flexible_work_incent"
    )

    print(
        f"\nLoading Policy:"
        f"\n{policy_key}\n"
    )

    raw_text = load_incent_text(
        policy_key
    )

    print(
        f"Raw Text Length:"
        f" {len(raw_text):,} chars"
    )

    result = extract_policy_json(
        raw_text
    )

    save_policy_json(
        policy_key,
        result
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2
        )
    )
