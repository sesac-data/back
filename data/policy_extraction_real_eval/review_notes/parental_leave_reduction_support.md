# Gold 검증 노트 — parental_leave_reduction_support

- 상태: **AI 초안 (Claude Opus 작성), 사람 검증 대기**
- 원문: `data/policy_extraction_real_eval/raw_text/parental_leave_reduction_support.txt`
- gold: `data/policy_extraction_real_eval/gold/parental_leave_reduction_support.json`

이 gold는 정답지 **초안**입니다. 아래 항목을 사람이 원문과 대조해 확정/수정해야 정식 gold가 됩니다. 특히 표·금액·tier 경계·인센티브 처리·중복규칙을 중점 확인하세요.

## 원문 금액 표 (raw 137~164행) 해석 근거

| 구분 | 1개월 지급액 | 연간총액 |
|---|---|---|
| 육아휴직지원금 · 만 12개월 이내 | (특례) 첫 3개월 100만원, 이후 30만원 | 570만원 |
| 육아휴직지원금 · 만 12개월 초과 | 30만원 | 360만원 |
| 남성 육아휴직 인센티브 (추가지원) | 10만원 | 120만원 |
| 육아기 근로시간 단축 지원금 · 일반 | 30만원 | 360만원 |
| 육아기 단축 인센티브 (추가지원) | 10만원 | 120만원 |

## 이 초안의 모델링 결정 (gold에 반영됨)

1. **육아휴직지원금을 자녀 연령으로 2개 항목 분리**
   - `SI-LEAVE-INFANT` (만 12개월 이내): `period_tiered` — tier1(1~3개월=1,000,000), tier2(4~12개월=300,000)
   - `SI-LEAVE-OLDER` (만 12개월 초과): `monthly_fixed` 300,000 / 12개월
2. **육아기 근로시간 단축 지원금 + 육아기단축 인센티브**를 하나의 `conditional_bonus`로 통합
   - `SI-WORKHOUR-REDUCTION`: base 300,000 / 12개월, bonus +100,000 (조건: 사업장 최초 육아기 단축 사용)
3. **남성 육아휴직 인센티브**는 `unresolved_rules`(UR-MALE-INCENTIVE, schema_gap)로 분리 — 아래 D-1 참조
4. **대체인력지원금 중복제한**은 `unresolved_rules`(UR-REPLACEMENT-DUPLICATE, ambiguous_target_policy)로 분리 — 아래 D-5 참조

## 이 초안이 의도적으로 "잡아내는" v6 추출 오류 (gold의 가치)

현재 v6 추출(`output/v6_gpt41_r3/parental_leave_reduction_support.json`)은 인센티브를 **독립 항목**으로 만들어 `SI-003`(conditional_bonus, base 30만 + bonus 10만), `SI-005`(동일)을 출력했습니다. 이는 **base 30만원을 중복 계산**합니다. 인센티브는 기존 지원금에 얹는 "추가지원"이므로 별도 30만원 base를 가지면 안 됩니다. → gold는 인센티브를 bonus/unresolved로만 표현해 이 중복을 오답으로 드러냅니다.

## 사람이 결정해야 할 항목 (D = Decision)

- **D-1 (가장 중요) 남성 육아휴직 인센티브 (+10만/월, raw 163행).**
  사업장별 남성육아휴직 1~3번째 사례에 대해 월 10만원 추가. 이 인센티브는 육아휴직지원금(만 12개월 이내/초과 **둘 다**)에 얹힙니다. 현재 schema의 `conditional_bonus`는 bonus를 항목 1개에만 붙입니다.
  → 결정 필요: (a) 두 육아휴직 항목 각각에 동일 bonus 중복 부착, (b) 육아휴직을 1개 항목으로 합치고 연령은 조건분기(현 schema 미지원 → OR/branch 필요), (c) 초안대로 unresolved 유지.
  → "1~3번째 사례" 라는 **건수 상한(count cap)** 은 현 schema에 표현 수단이 없음(별도 결정 필요).

- **D-2 육아기단축 인센티브 조건/상한 (raw 164행).**
  "육아기 근로시간 단축을 한 번도 사용하지 않은 사업장의 사업주가 최초 허용 시, 세 번째 허용 사례까지 월 10만원." 초안은 조건 `company.is_first_workhour_reduction_use = true` 하나로 단순화했습니다.
  → field 이름 확정 + "세 번째 사례까지" 건수 상한 처리 결정.

- **D-3 특례 200만원 (raw 162행).**
  "2025년 12월 31일 이전에 육아휴직을 사용한 경우 월 200만원." 초안의 tier1은 현행 **100만원**만 반영. 날짜 조건부 tier(legacy)는 미반영.
  → MVP 범위에서 제외할지, 날짜 조건 tier를 둘지 결정.

- **D-4 연간총액 한도 (570만/360만/120만).**
  초안은 월 단가·기간만 넣고 **연 한도(yearly cap)** 는 gold에 넣지 않았습니다. 계산 엔진에 연 한도 개념이 있으므로 추가 여부 결정.

- **D-5 대체인력지원금 중복제한 (raw 179행).**
  "육아휴직 특례 지원금은 육아휴직 대체인력인건비 지원을 포함하므로, 특례 지원받은 경우 육아휴직 대체인력지원금 전체 기간 중복지원 제한." 대상 정책 id가 `replacement_workshare_support`인지 별개 정책인지 불명확 → 초안은 `ambiguous_target_policy`.
  → 대상 id 확정 시 `combination_rules`의 `mutually_exclusive`로 승격.

- **D-6 지급제한(자격 배제) 조건 (raw 165~176행).**
  근로자 요건(사업주 배우자·직계존비속 제외, 고용보험 미가입 제외, 월평균 보수 124만원 미만 제외, 일부 외국인 제외)과 사업주 요건(공공기관·특정 업종·명단공개 사업주 제외). 초안에는 **미반영**.
  → 배제 조건을 gold 조건으로 인코딩할지 결정(특히 "월평균 보수 124만원 미만 제외"는 수치 조건이라 인코딩 용이).

- **D-7 "30일 이상" 조건의 단서 (raw 130행).**
  "30일(출산전후 휴가와 중복기간 제외) 이상 부여" 중 **중복기간 제외** 뉘앙스를 초안은 단순화(`duration_days >= 30`)했습니다. → 정밀화 여부 결정.

- **D-8 50%/50% 분할 지급 (raw 132~133행).**
  3개월 주기 50% + 복직 6개월 이상 계속고용 후 나머지 50%. 이는 **지급 시기**이지 금액이 아니므로 gold에서 의도적으로 제외. → 동의 여부 확인.

## 평가 하네스 한계 (자동 채점 전 처리 필요)

- **support_item_id 매칭 문제**: `policy_structure_evaluator`는 support_item을 `support_item_id`로 매칭합니다. gold는 의미 있는 안정 id(`SI-LEAVE-INFANT` 등)를 쓰지만, LLM 후보는 `SI-001`처럼 임의 id를 씁니다. → 라이브 후보 채점 전, **내용(calculation_type+금액) 기반으로 항목을 정렬·매칭하는 어댑터**가 필요합니다. (tier는 `(start_month,end_month)`로 내용 매칭되므로 안전)
- **evidence 비교**: 초안 gold는 의미(금액·구조)에 집중하기 위해 항목별 `evidence_snippets`를 **생략**했습니다(원문-substring 검증은 별도 validator가 담당). 더 엄격히 보려면 gold에 evidence를 추가하세요.
