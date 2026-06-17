# Gold(정답지) 작성·검증 상세 가이드

이 문서는 사람이 직접 gold JSON을 **채우고 검증**하는 방법을 단계별로 설명합니다.
함께 볼 문서: [GOLD_CONVENTIONS.md](GOLD_CONVENTIONS.md)(모델링 규칙), [README.md](README.md)(데이터셋 구조).

---

## 0. gold가 무엇이고 왜 직접 채워야 하나

- gold = **사람이 원문을 읽고 손으로 적은 "이게 정답이다" JSON**. LLM 추출을 채점하는 기준입니다.
- AI가 gold를 만들면 "자기 채점"이 되어 같은 실수를 못 잡습니다. 그래서 **최종 정답 권한은 사람**입니다.
- 현재 7개 문서에 **AI 초안**이 있습니다. 당신이 할 일은 이 초안을 원문과 대조해 **확정/수정**하는 것입니다(빈 파일을 처음부터 쓰는 것보다 훨씬 빠릅니다).

작업 대상 파일(문서당):
```
raw_text/{case_id}.txt        ← 원문 (읽기용, 수정 안 함)
gold/{case_id}.json           ← 당신이 채우는 정답지
review_notes/{case_id}.md     ← AI가 표시한 "결정 필요 항목(D-1, D-2 ...)" — 여기부터 보세요
```

---

## 1. 작업 순서 (한 문서당)

1. `review_notes/{case_id}.md`의 **D 항목**(결정 필요 사항)을 먼저 읽는다. AI가 헷갈린 지점이 다 적혀 있다.
2. `raw_text/{case_id}.txt`에서 **금액 표·지원대상·지원요건·지원내용** 영역을 읽는다.
3. `gold/{case_id}.json`을 열어 아래 §2~§5 규칙대로 항목을 채운다/고친다.
4. §6 체크리스트로 자가검증한다.
5. `python scripts/score_extraction_against_gold.py` 로 점수를 확인한다(§7).

---

## 2. JSON 전체 모양

```json
{
  "policy_id": "<문서 case_id 그대로>",
  "policy_name": "<원문 본문 제목 그대로>",
  "review_status": "needs_review",
  "support_items": [ ... ],
  "combination_rules": [ ... ],
  "unresolved_rules": [ ... ]
}
```

- `policy_id`: 파일명(case_id)과 동일하게. 예: `parental_leave_reduction_support`.
- `policy_name`: 원문 본문 제목 줄. 예: `육아휴직지원금, 육아기 근로시간 단축 지원금`.
- `review_status`: **항상 `"needs_review"`**. (gold라도 승인 정책이 아님)
- 나머지 3개 배열은 아래에서 설명.

> 팁: gold는 **"검사하고 싶은 사실"만** 적으면 됩니다. 채점기는 gold에 **있는 키만** 추출 결과와 비교합니다(없는 키는 안 봄). 그래서 evidence처럼 채점에 노이즈가 되는 건 일부러 비웁니다(§5.5).

---

## 3. support_items — 핵심

각 지원금(또는 그 변형)을 하나의 항목으로. 항목마다 **calculation_type을 먼저 정하고**, 타입별 필수 필드를 채웁니다.

### 3.1 calculation_type 고르는 법 (원문을 보고 판단)

| 원문이 이렇게 말하면 | 타입 |
|---|---|
| 단일 월정액 + 최대 기간 (예: "월 30만원, 최대 1년") | `monthly_fixed` |
| 기간별로 단가가 달라짐 (예: "첫 3개월 100만원, 이후 30만원") | `period_tiered` |
| 기본액 + 추가지원/인센티브 (예: "월 30만원 + 남성육아휴직 인센티브 10만원") | `conditional_bonus` |

### 3.2 monthly_fixed

```json
{
  "support_item_id": "SI-...",
  "calculation_type": "monthly_fixed",
  "monthly_amount": 300000,
  "max_months": 12,
  "conditions": [ ... ]
}
```
- `monthly_amount`: 원(숫자). "월 30만원" → `300000`.
- `max_months`: 최대 지원 개월. 원문에 상한이 **없으면 `null`** (추론 금지). 예: 대체인력은 사용 개월수가 변수 → `null`.

### 3.3 period_tiered

```json
{
  "support_item_id": "SI-...",
  "calculation_type": "period_tiered",
  "tiers": [
    { "start_month": 1, "end_month": 3,  "monthly_amount": 1000000 },
    { "start_month": 4, "end_month": 12, "monthly_amount": 300000 }
  ],
  "conditions": [ ... ]
}
```
- `tiers`: 기간 구간별 단가. `start_month`/`end_month`는 **포함(inclusive)**, **겹치거나 비면 안 됨**.
- "첫 3개월 100만원 → 이후 30만원, 연 570만원" → tier1(1~3, 1,000,000) + tier2(4~12, 300,000). (3×100 + 9×30 = 570만, 연간총액과 일치하는지 검산!)

### 3.4 conditional_bonus

```json
{
  "support_item_id": "SI-...",
  "calculation_type": "conditional_bonus",
  "monthly_amount": 300000,
  "max_months": 12,
  "bonuses": [
    {
      "bonus_id": "B-...",
      "monthly_amount": 100000,
      "max_months": 12,
      "conditions": [
        { "condition_id": "C-...", "field": "...", "operator": "eq", "expected": true }
      ]
    }
  ],
  "conditions": [ ... ]
}
```
- 기본액은 항목의 `monthly_amount`, 추가지원은 `bonuses[].monthly_amount`.
- ⚠️ **가장 흔한 실수**: 인센티브를 "기본액 30만 + 추가 10만"의 **독립 항목**으로 만들면 base 30만을 **중복 계산**합니다. 인센티브는 반드시 **부모 항목의 bonus**로 넣으세요.

### 3.5 conditions (조건)

```json
{ "condition_id": "C-...", "field": "employee.child_age", "operator": "lte", "expected": 12 }
```
- `field`: `영역.속성` 형식. 단위는 필드명에 녹입니다(별도 `unit` 필드 금지).
  - 자주 쓰는 예: `employee.child_age`(만 나이), `employee.child_age_months`(개월), `employee.weekly_work_hours_before/after`, `employee.daily_reduction_hours`, `leave_event.duration_days`, `leave_event.duration_months`, `company.employee_count`, `company.is_priority_support_enterprise`, `company.prohibits_wage_reduction`.
- `operator`: `eq, neq, gt, gte, lt, lte, in, not_in` 중 하나.
- `expected`: 기대값(숫자/문자열/true/false). 원문에 없는 숫자를 만들지 마세요.
- `condition_id`: 후보 JSON **전체에서 유일**하게. bonus 안 조건도 포함.
- "주 35시간 이상 근무" → `{field:"employee.weekly_work_hours_before", operator:"gte", expected:35}`.
- "또는(OR)" 조건(예: 만 12세 이하 **또는** 초등 6학년 이하)은 현 스키마 미지원 → 대표 1개만 넣고 전체는 `unresolved_rules`로(§4.2).

---

## 4. combination_rules vs unresolved_rules — 헷갈리는 부분

### 4.1 combination_rules (정책 간 관계, 대상이 명확할 때만)

```json
{ "rule_id": "CR-...", "rule_type": "mutually_exclusive", "target_policy_ids": ["other_policy_id"], "reason": "근거", "evidence_snippets": ["원문 그대로"] }
```
- `rule_type`: `mutually_exclusive`(동시 수급 불가) / `requires`(선행 필요) / `allowed_with`(허용).
- 대상 정책 id가 **명확하고 무조건**일 때만. 애매하면 §4.2로.

### 4.2 unresolved_rules (현 스키마로 표현 못 하는 규칙 — 버리지 말고 여기에)

```json
{ "rule_id": "UR-...", "rule_type": "schema_gap" }
```
원문에 있지만 스키마로 안전하게 못 담는 규칙은 **누락하지 말고** 여기에 분류:

| 상황 | rule_type |
|---|---|
| 만 12세 이하 **또는** 초등 6학년 이하 (OR 조건) | `unsupported_or_condition` |
| 전년도 피보험자수 30%, 최대 30명 (복합 인원 한도) | `complex_headcount_cap` |
| 기존 장려금과 사용기간 합산 최대 1년 | `shared_duration_cap` |
| 월 출퇴근 누락 3일 초과 시 해당월 부지급 | `monthly_exclusion_rule` |
| 대상 정책이 누구인지 불명확한 중복제한 | `ambiguous_target_policy` |
| 조건부 중복제한(예: "특례 받은 경우에만") | `unsupported_combination_rule` |
| 기타 표현 불가 | `schema_gap` |

---

## 5. 무엇을 **넣지 않는지** (의도적 생략)

- **5.1 지급 시기/절차**: 50%/50% 분할 지급, 신청 주기, 인수인계 기간 → 금액이 아니므로 생략.
- **5.2 신청방법/제출서류/문의/Q&A 절차**: 생략.
- **5.3 연 한도**: 월단가×기간으로 유도되면(예: 30만×12=360만) 중복으로 넣지 않음.
- **5.4 정책 단위 자격 배제 조건**(지급제한: 배우자·직계존비속, 월보수 124만원 미만 등): 현 스키마에 정책 단위 조건 슬롯이 없어 support_item에 억지로 넣지 않음. 중요하면 `review_notes`에 기록(또는 합의되면 별도 확장).
- **5.5 evidence_snippets**: gold에서는 **비웁니다**(의미·금액 채점에 집중; 원문-substring 검증은 별도 validator 담당). 단 `policy_name`은 반드시 채움.

---

## 6. 자가검증 체크리스트 (제출 전)

- [ ] `review_status`가 `"needs_review"`.
- [ ] 모든 금액이 **원문에 실제로 있는 숫자**(만원 단위 대조). 없는 값 날조 금지.
- [ ] period_tiered의 tier가 **겹치지 않고 빈 구간 없음**. (검산: tier 합 = 연간총액?)
- [ ] 인센티브/추가지원이 **독립 항목이 아니라 bonus**로 들어갔는가? (base 중복 금지)
- [ ] OR 조건/복합 한도/월부지급/조건부중복이 `unresolved_rules`로 갔는가?
- [ ] `support_item_id` / `condition_id` / `bonus_id` / `rule_id`가 전부 유일.
- [ ] JSON 파싱됨: `python -c "import json;json.load(open('data/policy_extraction_real_eval/gold/<case>.json',encoding='utf-8'))"`

---

## 7. 채점 실행과 점수 읽는 법

```powershell
python scripts\score_extraction_against_gold.py
# 특정 추출 결과와 비교하려면:
python scripts\score_extraction_against_gold.py --output-dir output\v6_gpt41_preproc
```

출력 예시:
```
document                            score  items g/c/m  errors
parental_leave_reduction_support     79.2  3/5/3      missing_condition:3, value_mismatch:2
```
- `score`: gold가 주장한 사실 중 추출이 맞춘 비율(0~100).
- `items g/c/m`: gold 항목수 / 추출 항목수 / 내용정렬로 매칭된 항목수.
- `errors`(오류 유형 = 어디가 다른지):

| 오류 | 의미 | 보통 원인 |
|---|---|---|
| `value_mismatch` | 값/타입 불일치 | calculation_type이 다름(예: 추출 monthly_fixed인데 gold conditional_bonus) |
| `amount_mismatch` | 금액 불일치 | monthly_amount/연액 숫자가 다름 |
| `tier_mismatch` | tier 불일치 | 구간 경계·단가가 다르거나 tier 자체가 없음 |
| `missing_condition` | 조건 누락 | gold가 기대한 조건을 추출이 안 만듦 |
| `missing_field` | 항목/필드 누락 | gold 항목에 대응하는 추출 항목이 없음(또는 bonus 누락) |

> 주의: 현재 점수는 **초안 gold 기준**입니다. `score`가 낮다고 무조건 추출이 틀린 건 아닙니다 — **gold 초안이 틀렸을 수도** 있으니, 낮은 항목은 원문과 양쪽을 같이 보세요. 그게 바로 검증 작업입니다.

---

## 8. 워크플로 요약

```
review_notes의 D항목 확인
  → 원문 표/요건 정독
    → gold JSON 수정 (§2~§5)
      → 체크리스트 (§6)
        → score 실행 (§7)
          → 낮은 점수 문서는 원문·gold·추출 3자 대조로 원인 규명
            → gold 확정(또는 추출 개선 과제로 분리)
```

gold 7개가 사람-확정되면, 이후 어떤 프롬프트/모델/크롤링 변경도 이 점수로 **객관 비교**할 수 있습니다.
