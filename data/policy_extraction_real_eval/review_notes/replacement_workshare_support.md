# Gold 검증 노트 — replacement_workshare_support (대체인력 지원금)

- 상태: **AI 초안 (Claude Opus 작성), 사람 검증 대기**
- 원문: `data/policy_extraction_real_eval/raw_text/replacement_workshare_support.txt`
- gold: `data/policy_extraction_real_eval/gold/replacement_workshare_support.json`
- 원본 URL: https://www.worklife.kr/website_renew/index/employerSupport/substitute_worker_subsidy.asp

이 gold는 정답지 **초안**입니다. 아래 항목을 사람이 원문과 대조해 확정/수정해야 정식 gold가 됩니다.
특히 표의 금액 셀, 회사 규모(피보험자수) 분기, 기간(개월수) 처리, 80% 임금 상한, 중복지원 제한을 중점 확인하세요.

## 원문 금액 표 (raw 159~171행) 해석 근거

| 구분 | 피보험자수 | 1개월 최대 지급액 |
|---|---|---|
| 육아휴직 / 출산전·후휴가 / 유산·사산휴가 | 30인 미만 | 140만원 (1,400,000) |
| 육아휴직 / 출산전·후휴가 / 유산·사산휴가 | 30인 이상 | 130만원 (1,300,000) |
| 육아기 근로시간 단축 | 공통 | 120만원 (1,200,000) |

- 이 금액들은 **월별 최대 지급액(monthly cap)** 이며, 실제 지급액 = 위 금액 × **대체인력을 사용한 개월수**(raw 154~157행). 사용 개월수는 가변(역에 의해 산정, 잔여일수는 일할).
- 따라서 **max_months는 명시되지 않음 → null** 로 둠. 표의 셀 값을 절대 합치지 않고 각 셀을 별도 항목으로 분리.

## 이 초안의 모델링 결정 (gold에 반영됨)

1. **표의 3개 금액 셀을 3개의 독립 `monthly_fixed` support_item으로 분리**
   - `SI-LEAVE-UNDER30`: 1,400,000 / month — 조건: 휴가유형 ∈ {육아휴직, 출산전후휴가, 유산·사산휴가} AND `company.insured_count < 30`
   - `SI-LEAVE-OVER30`: 1,300,000 / month — 동일 휴가유형 AND `company.insured_count >= 30`
   - `SI-WORKHOUR-REDUCTION`: 1,200,000 / month — 조건: 휴가유형 = 육아기 근로시간 단축 (피보험자수 공통, 규모 분기 없음)
   - 세 항목 모두 `max_months = null` (사용 개월수 가변).
2. **휴가유형 분기**를 `leave_event.leave_type` 조건으로 인코딩. 처음 두 항목은 3개 유형 OR이므로 `operator="in"` + 배열로 표현(현 schema가 `in`을 지원한다는 가정; 미지원 시 D-2 참조).
3. **80% 임금 상한**(raw 174행, "월별 지원액은 임금액의 80%를 초과할 수 없음")은 월 단가가 아니라 개별 대체인력 임금에 종속된 상한이라 schema로 표현 불가 → `unresolved_rules`(UR-WAGE-80PCT-CAP, schema_gap).
4. **가변 기간 / 인수인계 기간 포함**(raw 154~157, 173)을 `unresolved_rules`(UR-DURATION-VARIABLE, shared_duration_cap)로 분리. max_months=null의 근거 메모.
5. **고용조정(감원) 지급제한**(raw 147~153)을 `unresolved_rules`(UR-EMPLOYMENT-ADJUSTMENT-EXCLUSION, schema_gap)로 분리 — 정책 단위 배제 조건이라 support_item 조건으로 강제 인코딩하지 않음(규약 6).
6. **육아휴직 특례 중복지원 제한**(raw 203행)을 `unresolved_rules`(UR-SPECIAL-CASE-DUPLICATE, unsupported_combination_rule)로 분리 — 아래 D-5.

## 이 초안이 의도적으로 "잡아내는" v6 추출 오류 (gold의 가치)

v6 추출(`output/v6_gpt41_r3/replacement_workshare_support.json`)의 문제:
- 금액 자체는 1,400,000 / 1,300,000 / 1,200,000 으로 정확히 읽음(이 부분은 일치).
- 그러나 **휴가유형 조건을 전혀 달지 않음.** 30인 미만/이상은 회사 규모 분기일 뿐인데, 이것이 어떤 휴가유형(육아휴직·출산전후·유산사산)에만 적용되고 육아기 단축(120만, 규모 무관)은 별개라는 **표의 행 구조를 놓침**. v6의 SI-001/SI-002는 휴가유형 제한 없이 단지 규모 조건만 가짐 → gold는 `leave_event.leave_type` 조건을 추가해 이 누락을 오답으로 드러냄.
- v6는 `field`를 `employee.insured_person_count`로 썼으나, 피보험자수는 **사업장 규모**이므로 gold는 `company.insured_count`로 정정.
- v6는 `company.is_priority_support_enterprise = true` 조건을 모든 항목에 넣었음. 우선지원대상기업은 정책 전체의 자격(대상)이지 항목별 분기 조건이 아니므로 gold에서는 제외(필요 시 D-3에서 정책 단위 자격으로 승격 검토).
- v6는 중복지원 제한·고용조정 제한을 모두 `schema_gap`으로만 처리. gold는 중복지원 제한을 `unsupported_combination_rule`로 세분화.

## 사람이 결정해야 할 항목 (D = Decision)

- **D-1 (가장 중요) 표의 행/열 매핑.**
  표가 "육아휴직 / 출산전후 / 유산·사산휴가" 행(30인 기준 1.4M / 1.3M)과 "육아기 근로시간 단축" 행(공통 1.2M)으로 나뉜다는 해석이 맞는지 원문 확인. 초안은 이 해석으로 3항목 분리. (원문 raw 162~171행은 셀이 줄바꿈으로 흩어져 있어 사람 확인 필요.)

- **D-2 휴가유형 OR 조건 표현(`operator="in"`).**
  처음 두 항목은 3개 휴가유형 중 하나면 적용 → `in` + 배열로 인코딩. 현 schema/validator가 `in` 연산자와 배열 expected를 지원하지 않으면, 대표 1개(예: parental_leave)만 넣고 OR 전체를 `unresolved_rules`(unsupported_or_condition)로 분리해야 함. 규약 3 참조.

- **D-3 우선지원대상기업 자격(raw 132~133).**
  "우선지원대상기업 사업주"가 정책 전체 대상 요건. 정책 단위 자격을 gold에 인코딩할 슬롯이 없어 초안은 제외. 별도 자격 슬롯 도입 여부 결정.

- **D-4 특례(만 12개월 이내 자녀) 단가(raw 172행).**
  "특례: 만 12개월 이내 자녀, 3개월 이상 연속 부여 시 첫 3개월 월 100만원, 이후 월 30만원 (2025-12-31 이전 사용 시 월 200만원)." 이는 표 기본 단가와 **다른 별도 단가 체계**(period_tiered, 100만→30만, legacy 200만). 초안은 이를 미반영(표 기본값만 모델링). 특례를 별도 period_tiered support_item으로 추가할지, 그리고 raw 203행의 중복제한과의 관계를 어떻게 둘지 결정 필요.
  → 결정 시: 특례 항목 추가(SI-LEAVE-SPECIAL, period_tiered) + 날짜 조건부 legacy tier 처리.

- **D-5 육아휴직 특례 중복지원 제한(raw 203행).**
  "육아휴직 특례 지원금은 육아휴직 대체인력인건비 지원을 포함하므로, 특례를 지원받은 경우 육아휴직 대체인력지원금 전체 기간 중복지원 제한." 조건부 배제(특례를 받은 경우에만)라 현 schema로 표현 불가 → `unsupported_combination_rule`. 대상 정책 id는 `parental_leave_reduction_support`의 육아휴직 특례로 추정(상호 참조: 그 문서의 D-5와 짝). 확정 시 `combination_rules`의 `mutually_exclusive`로 승격 검토.

- **D-6 80% 임금 상한(raw 174행).**
  "대체인력지원금의 월별 지원액은 해당 대체인력에게 지급한 임금액의 80%를 초과할 수 없음." 개별 임금 종속이라 schema 미표현. UR-WAGE-80PCT-CAP(schema_gap)로 분리. 추천 엔진이 임금 정보를 가질 수 없으면 그대로 둠.

- **D-7 고용조정(감원) 지급제한(raw 147~153).**
  대체인력 고용 전 3개월~후 1년 사이 고용조정(감원) 시 지급 제한. 정책 단위 배제 조건이라 support_item 조건으로 강제하지 않음(규약 6). UR로만 기록. 인코딩 여부 결정.

- **D-8 지급제한(자격 배제) 조건(raw 175~188행).**
  근로자 요건(사업주 배우자·직계존비속 제외, 고용보험 미가입 제외, **월평균 보수 124만원 미만 제외**, 일부 외국인 제외)과 사업주 요건(국가·지자체·공공기관, 유흥/사행업종, 명단공개·공표 사업주 제외). 규약 6에 따라 정책 단위 배제 조건은 미모델링. 특히 "월평균 보수 124만원 미만 제외"는 수치 조건이라 인코딩이 용이 — 추천 정확도에 중요하면 우선 인코딩 검토.

- **D-9 신청 시기·50% 분할(raw 189~196행).**
  3개월마다 신청, 2026-01-01 전 고용 시 50% 선지급/50% 후지급. 금액이 아닌 시기/절차이므로 규약 7에 따라 gold에서 제외. 동의 여부 확인.

## 평가 하네스 한계 (자동 채점 전 처리 필요)

- **support_item_id 매칭**: 평가기는 id로 매칭하나 gold는 의미 id(SI-LEAVE-UNDER30 등), LLM 후보는 SI-001 등 임의 id → 내용(calculation_type+금액+조건) 기반 정렬 어댑터 필요.
- **`in` 연산자 / 배열 expected** 지원 여부가 채점에 영향(D-2). validator가 미지원이면 gold 표현 변경 필요.
- **evidence**: 규약 8에 따라 항목별 evidence_snippets 생략(원문-substring 검증은 별도 validator).
