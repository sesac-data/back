# Gold 작성 규약 (모델링 규칙)

이 문서는 7개 육아 관련 사업주 지원금 문서의 **gold(정답지) 초안**을 일관되게 작성하기 위한 규칙입니다.
gold는 `policy_structure_evaluator`가 LLM 추출 후보를 의미 비교(채점)할 때 쓰는 사람-확정 기준입니다.

상태: **AI 초안용 잠정 규약 — 최종은 사람(ksm) 사인오프 필요.** 아래 결정값은 parental 문서의 D-1~D-8 검토에서 도출했습니다.

## 0. 출력 형식 (v6 호환 flat 구조)

평가기는 gold에 존재하는 키만 후보와 비교합니다. 따라서 gold는 v6이 내는 flat 필드명을 그대로 씁니다.

```json
{
  "policy_id": "<incent_key>",
  "policy_name": "<원문 본문 제목>",
  "review_status": "needs_review",
  "support_items": [],
  "combination_rules": [],
  "unresolved_rules": []
}
```

support_item 구조:

- 공통: `support_item_id`, `calculation_type`, `conditions`
- `monthly_fixed`: `monthly_amount`, `max_months`
- `period_tiered`: `tiers: [{start_month,end_month,monthly_amount}]`
- `conditional_bonus`: `monthly_amount`, `max_months`, `bonuses: [{bonus_id,monthly_amount,max_months,conditions}]`
- condition: `condition_id`, `field`, `operator`, `expected`

## 1. calculation_type 선택

- 기간별 단가 변동(첫 N개월 → 이후) = `period_tiered`
- 기본액 + 추가지원/인센티브 = `conditional_bonus` (추가분은 `bonuses`)
- 그 외 단일 월정액 = `monthly_fixed`

## 2. 인센티브/추가지원 처리 (D-1, D-2)

- 추가지원이 **특정 한 지원금 위에** 얹히면 → 그 항목의 `bonuses`로 넣고 `calculation_type="conditional_bonus"`.
  - **절대 별도 "기본액+추가액" 독립 항목으로 만들지 않는다** (base 중복 계산 방지). v6의 대표 오류가 이것.
- 추가지원이 **여러 항목에 동시에** 걸치거나(예: 남성육아휴직 인센티브가 만12개월 이내/초과 둘 다에 적용), **건수 상한**("1~3번째 사례", "세 번째까지")을 동반하면:
  - 현 schema로 안전 표현 불가 → `unresolved_rules`에 `rule_type="schema_gap"`로 분리하고 노트에 기록.
  - 단, 단일 항목에 깔끔히 붙고 조건이 boolean으로 표현되면 `bonuses`로 인코딩(건수 상한은 노트로 flag).

## 3. 자녀 연령 등 분기 조건 (D-7)

- 동일 지원금이 연령대로 단가가 다르면(만 12개월 이내 vs 초과) **연령 조건이 붙은 별도 support_item으로 분리**.
- "또는"(OR) 조건(예: 만 12세 이하 **또는** 초등 6학년 이하)은 현 schema 미지원 → 두 조건 중 대표 1개를 넣고 OR 전체는 `unresolved_rules`(`unsupported_or_condition`)로 분리 + 노트.

## 4. 연 한도(yearly cap) (D-4)

- `tiers` 또는 `monthly_amount × max_months`로 연간총액이 **유도되면 중복 인코딩하지 않는다**(예: 30만×12=360만).
- 월 단가·기간으로 유도되지 않는 독립적 연/기업 단위 상한만 별도 표현(현재는 대부분 `unresolved_rules`).

## 5. 중복수급/조합 규칙 (D-5)

- 대상 정책 id가 명확하고 **무조건적** 배제면 → `combination_rules` (`mutually_exclusive`/`requires`/`allowed_with`).
- 대상이 불명확하면 → `unresolved_rules` `ambiguous_target_policy`.
- 대상은 대략 알지만 **조건부**(예: "특례를 받은 경우에만 중복 제한")라 현 schema로 표현 불가면 → `unresolved_rules` `unsupported_combination_rule` + 노트에 추정 대상 id 기록.

## 6. 지급제한(자격 배제) 조건 (D-6)

- 현 schema는 **정책 단위 배제 조건** 슬롯이 없음(조건은 support_item에 붙음).
- 따라서 gold 초안에서는 배제 조건(사업주 배우자·직계존비속, 미가입, 월보수 124만원 미만, 공공기관/특정업종/명단공개 등)을 **support_item 조건으로 강제 인코딩하지 않고**, 노트에 "정책 단위 배제 조건 미모델링(schema gap)"으로 기록한다.
- 수치로 명확하고 추천 정확도에 중요한 항목(예: 월평균 보수 124만원 미만 제외)은 노트에 우선순위로 표시.

## 7. 지급 시기/절차 (D-8)

- 50%/50% 분할, 신청 주기, 인수인계 기간 등 **금액이 아닌 시기/절차**는 gold에서 제외(추천 엔진은 총액 기준).

## 8. evidence

- 의미(금액·구조) 채점에 집중하기 위해 gold에서는 항목별 `evidence_snippets`를 **생략**한다(원문-substring 검증은 별도 validator 담당).
- 단 `policy_name`은 반드시 채운다.

## 9. id 규칙 (자동 채점 한계)

- support_item_id는 의미 있는 안정 id 사용(`SI-LEAVE-INFANT` 등). condition_id/bonus_id/rule_id도 의미 기반.
- 평가기는 support_item을 id로 매칭하므로, **라이브 후보 자동 채점에는 내용 기반 정렬 어댑터가 별도로 필요**(tier는 `(start,end)`로 내용 매칭됨). 옵션 (c) 작업.

## 10. 산출물 (문서별 3+1 파일)

```text
raw_text/{case_id}.txt        원문 복사
gold/{case_id}.json           정답지 초안
metadata/{case_id}.json       case_id/policy_name/source_url/source_type/collected_at/notes
review_notes/{case_id}.md     모델링 결정 + 사람 검증 포인트(D 항목)
```
