# Gold 검증 노트 — childcare_flexible_start_support

- 상태: **AI 초안 (Claude Opus 작성), 사람 검증 대기**
- 원문: `data/policy_extraction_real_eval/raw_text/childcare_flexible_start_support.txt`
- gold: `data/policy_extraction_real_eval/gold/childcare_flexible_start_support.json`
- 정책명: 육아기 10시 출근 지원 (워라밸장려금) / 워라밸일자리 장려금(육아기 10시 출근제)

이 gold는 정답지 **초안**입니다. 아래 항목을 사람이 원문과 대조해 확정/수정해야 정식 gold가 됩니다.

## 원문 금액 구조 (raw 143~155행) 해석 근거

| 구분 | 내용 |
|---|---|
| 지원수준 (단축 근로자 1인당) | 월 30만원 |
| 지원기간 | 지급일로부터 최대 1년 (= 12개월) |
| 지원한도 | 전년도 말일 고용보험 피보험자 수의 30% (10명 미만 시 3명) 한도, 최대 30명 |
| 합산 | 워라밸일자리 장려금(소정근로시간단축) 지원인원과 합산 산정 |
| 지급 주기 | 1개월 단위 산정, 3개월 주기 신청·지급 (= 시기/절차, gold 제외) |

→ 단일 월정액 구조. 기간별 단가 변동·인센티브·추가지원 없음 → `monthly_fixed` 1개 항목.

## 이 초안의 모델링 결정 (gold에 반영됨)

1. **support_item 1개 (`SI-FLEX-START`, `monthly_fixed`)**: 월 30만원(`monthly_amount=300000`), 최대 1년(`max_months=12`).
2. **자격 조건 10개**를 support_item의 `conditions`로 인코딩:
   - 우선지원대상기업/중견기업 사업주(`company.is_priority_support_enterprise = true`)
   - 육아기 자녀 연령(`employee.child_age lte 12`) — 단, OR 조건이라 D-1 참조
   - 단축 전 6개월 이상 주 35시간 이상 근무(`weekly_work_hours_before gte 35`)
   - 단축 후 주 소정근로 30시간 초과~35시간 이하(`weekly_work_hours_after gt 30` + `lte 35`)
   - 매일 1시간 단축(`daily_reduction_hours gte 1`)
   - 임금삭감 금지 / 취업규칙 규정 / 전자·기계적 근태관리 (boolean 3종)
   - 최소 1개월 이상 단축(`leave_event.duration_months gte 1`)
3. **evidence_snippets는 항목·조건 단위 모두 생략** (규약 8). v6 후보가 넣은 evidence는 모두 제거.
4. **schema gap 6건을 `unresolved_rules`로 분리** (D-1~D-6 참조).

## 이 초안이 의도적으로 "잡아내는" v6 추출 오류 (gold의 가치)

- v6(`output/v6_gpt41_r3/childcare_flexible_start_support.json`)은 `employee.child_age lte 12`만 넣고 **"또는 초등학교 6학년 이하" OR 분기를 누락**했습니다. gold는 대표 1개 조건을 두되 OR 전체를 `UR-CHILD-AGE-OR`(unsupported_or_condition)로 분리해 이 누락을 드러냅니다.
- v6은 항목·조건마다 `evidence_snippets`를 채웠습니다 → 규약 8 위반. gold는 모두 제거.
- 그 외 v6의 unresolved 분리(월별 배제·피보험자 한도·합산 한도·중복 규칙)는 방향이 맞아 유지하되 id/rule_type을 규약에 맞춰 정리했습니다.

## 사람이 결정해야 할 항목 (D = Decision)

- **D-1 자녀 연령 OR 조건 (raw 132~133행).**
  "육아기* 자녀 ... * 만 12세 이하 **또는** 초등학교 6학년 이하". 현 schema는 OR 미지원. 초안은 `employee.child_age lte 12` 대표 1개만 두고 OR 전체를 `UR-CHILD-AGE-OR`로 분리.
  → 결정 필요: (a) 초안 유지, (b) "초등 6학년 이하" 표현용 field 추가.

- **D-2 월별 지급제한 — 출퇴근기록 누락 (raw 140행).**
  "출퇴근기록 누락일수가 월 3일 초과(4일 이상) 시 해당월 장려금 미지급." 월 단위 부지급 규칙이라 총액 모델에 표현 불가 → `UR-ATTENDANCE-EXCLUSION`(monthly_exclusion_rule). → MVP 제외/유지 확인.

- **D-3 월별 지급제한 — 연장근로 (raw 142행).**
  "연장근로 제한(월 10시간 초과시 해당월 부지급)" → `UR-OVERTIME-EXCLUSION`(monthly_exclusion_rule). → 동일 확인.

- **D-4 피보험자수 한도 (raw 151~153행).**
  "전년도 말일 고용보험 피보험자 수의 30%(10명 미만 시 3명) 한도, 최대 30명." 기업 단위 인원 상한 → `UR-HEADCOUNT-CAP`(complex_headcount_cap). 월 단가·기간으로 유도되지 않는 독립 상한이라 별도 분리. → 모델링 방식 확인.

- **D-5 합산 한도 (raw 154행, 199~200행).**
  "워라밸일자리 장려금(소정근로시간단축) 지원인원과 합산 산정" + Q4 "기존 워라밸일자리장려금(소정근로시간단축) 지원 시 사용 기간 합산하여 최대 1년." 대상 정책 추정 id = `working_hour_reduction_support`(소정근로시간 단축 지원). 인원·기간 양쪽 합산이라 현 schema 표현 불가 → `UR-SHARED-DURATION-CAP`(shared_duration_cap). → 대상 id 확정 시 combination_rules 승격 검토.

- **D-6 법정 육아기 근로시간 단축과의 중복 (raw 192~195행).**
  Q3 "육아기 근로시간 단축(법정)과 10시 출근제(자율)는 별개이나 사용기간 중복 시 하나의 지원금만 지원." 조건부(기간 중복 시에만) 배제라 현 schema 표현 불가 → `UR-STATUTORY-REDUCTION-OVERLAP`(unsupported_combination_rule). 추정 대상 = 육아기 근로시간 단축 지원금(`parental_leave_reduction_support`의 단축 항목). → 대상 id/조합 방식 확정.

## 규약 6 관련 (정책 단위 배제 조건 미모델링)

- 본 문서에는 보수 하한·사업주 배우자 제외 등 명시적 배제 조건이 없어 별도 미모델링 항목 없음.

## 지급 시기/절차 (규약 7 — gold 제외)

- "1개월 단위 산정, 3개월 주기 신청·지급", "최초 활용 다음 달부터 3개월마다 신청"은 시기/절차이므로 gold에서 의도적으로 제외.

## 평가 하네스 한계

- **support_item_id 매칭**: gold는 안정 id(`SI-FLEX-START`)를 쓰나 LLM 후보는 `SI-001`을 씀 → 내용(calculation_type+금액) 기반 정렬 어댑터 필요.
- **evidence 비교**: 규약 8에 따라 gold에서 evidence 생략(원문-substring 검증은 별도 validator 담당).
