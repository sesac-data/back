# Gold 검증 노트 — flexible_work_incent (유연근무 장려금)

- 상태: **AI 초안 (Claude Opus 작성), 사람 검증 대기**
- 원문: `data/policy_extraction_real_eval/raw_text/flexible_work_incent.txt`
- gold: `data/policy_extraction_real_eval/gold/flexible_work_incent.json`
- 원본 URL: https://www.worklife.kr/website_renew/index/employerSupport/flexible_work_bonus.asp

이 gold는 정답지 **초안**입니다. 아래 항목을 사람이 원문과 대조해 확정/수정해야 정식 gold가 됩니다.
특히 금액·2배 지원 처리·근태관리 제외 규칙·지원한도(headcount)를 중점 확인하세요.

## 원문 지원내용 표 (raw 152~169행) 해석 근거

| 유형 | 1개월 지급액 | 최대 지급액(1년) | 비고 |
|---|---|---|---|
| 재택·원격근무 | 20만원 | 240만원 | 월 4일 이상 활용 |
| 육아기 시차출퇴근 / 선택근무 | 30만원 | 360만원 | 월 6시간 이상 단축, 단축일에 1시간 이상 단축 |
| (공통) 육아기 자녀 근로자 | **2배 지원** | 1년간 최대 720만원 | 재택·원격·선택근무에 적용 |

- 일반 근로자: 1년간 최대 360만원 / 육아기 근로자: 1년간 최대 720만원 (raw 153행).
- max_months는 240만÷20만=12, 360만÷30만=12 로 유도 → 두 항목 모두 `max_months=12`.

## 이 초안의 모델링 결정 (gold에 반영됨)

1. **base 항목 2개로 분리**
   - `SI-REMOTE-TELEWORK` (재택·원격근무): base 200,000 / 12개월, 조건 = type∈{재택,원격} AND 월 4일 이상.
   - `SI-SELECTIVE-STAGGERED` (육아기 시차출퇴근·선택근무): base 300,000 / 12개월, 조건 = type∈{육아기 시차출퇴근, 선택근무} AND 월 6시간 이상 단축 AND 단축일 1시간 이상 단축.
2. **육아기 자녀 2배 지원**을 각 항목의 `bonus`로 인코딩 (calculation_type=`conditional_bonus`)
   - 2배 = base와 동일한 추가액이므로 bonus monthly_amount = base와 동일(200,000 / 300,000), 조건 `employee.has_childcare_age_child = true`.
   - 단, 이것은 **배수(×2)**이고 **두 항목에 동시에 걸치므로** 현 schema의 단일-항목 fixed-bonus 의미와 정확히 일치하지 않음 → `unresolved_rules`(UR-CHILDCARE-DOUBLE-MULTIPLIER, schema_gap)로도 flag. 아래 D-1 참조.
3. **지급제한/근태관리·연장근로 제외 규칙**은 정책 단위 조건이라 support_item 조건으로 강제 인코딩하지 않고 unresolved/노트로 기록 (D-2, D-3).
4. **지원한도(headcount cap)** 와 **중복수급 제한**은 unresolved_rules로 분리 (D-4, D-5).

## 이 초안이 의도적으로 "잡아내는" v6 추출 오류 (gold의 가치)

현재 v6 추출(`output/v6_gpt41_r3/flexible_work_incent.json`)은 **2배 지원을 독립 항목 `SI-003`(monthly_amount 600,000)** 로 만들었습니다.
이는 base(재택·원격 20만 / 선택 30만)를 **중복 계산**하고, 600,000이라는 원문에 없는 합성 금액을 만들어냅니다(원문은 ×2 배수만 명시).
→ gold는 2배를 base 위의 bonus로만 표현해 이 중복·합성 금액을 오답으로 드러냅니다.
또한 v6는 "주 35~40시간" 근로조건을 두 항목 조건으로 강제 인코딩했으나, 이는 정책 단위 자격요건(개별 근로자 매칭 변수 아님)에 가까워 본 gold에서는 제외했습니다(D-2).

## 사람이 결정해야 할 항목 (D = Decision)

- **D-1 (가장 중요) 육아기 자녀 2배 지원 (raw 168행 "육아기 자녀를 둔 근로자의 재택·원격·선택근무는 2배 지원").**
  이는 고정 추가액이 아니라 **배수(×2)** 이며, 재택·원격·선택근무 **여러 항목에 동시 적용**됩니다.
  초안은 각 항목에 base와 동일액 bonus(boolean 조건)로 인코딩하고 `UR-CHILDCARE-DOUBLE-MULTIPLIER`(schema_gap)로도 표시했습니다.
  → 결정 필요: (a) 초안대로 bonus+unresolved 병행, (b) multiplier 전용 필드 신설, (c) unresolved만 두고 bonus 제거.
  주의: 시차출퇴근은 본래 "육아기 자녀를 둔 근로자에 한하여 지원"(raw 132행)이므로 시차출퇴근 항목은 사실상 항상 육아기 조건 → 2배 적용 범위(시차출퇴근 포함 여부) 재확인 필요.

- **D-2 근로조건(주 35~40시간) 및 유형/근태 자격요건 (raw 139, 145~151행).**
  주 35~40시간, 근로계약서 변경, 전자·기계적 근태관리 등은 **정책 단위 자격요건**입니다.
  초안은 (육아휴직 gold의 D-6 규약과 동일하게) support_item 조건으로 인코딩하지 않았습니다.
  → 수치 조건인 "주 35~40시간"을 매칭 변수로 인코딩할지 결정.

- **D-3 선택근무 연장근로 12시간 초과 제외 (raw 149행).**
  "정산기간을 평균하여 주당 연장근로시간이 12시간을 초과하는 경우 해당 정산기간 전체에 대해 동 제도를 활용하지 않은 것으로 산정."
  이는 부지급(제외) 규칙 → `UR-SELECTIVE-OVERTIME-EXCLUSION`(schema_gap)으로 분리. 조건 인코딩 여부 결정.

- **D-4 지원한도 headcount cap (raw 169행, Q2).**
  "직전년도 말일 기준 피보험자수의 30% 한도 내 최대 70명"(피보험자 10명 미만/신규 성립은 최대 3명).
  금액이 아닌 인원 상한 → `UR-HEADCOUNT-CAP`(complex_headcount_cap)로 분리. (v6도 동일 처리)

- **D-5 동일 사업장 유연근무 장려금 지원 이력자 제외 (raw 195행, Q1).**
  "동일 사업장에서 유연근무 장려금 지원 이력이 있는 근로자에 대해서는 더 이상 지원받을 수 없음."
  중복/이력 기반 배제 → `UR-DUPLICATE-FLEXIBLE-HISTORY`(unsupported_combination_rule)로 분리. 정책 id/표현 확정 필요.

- **D-6 연간총액 한도 (240만/360만, 육아기 720만).**
  월 단가×12로 유도되므로 규약 4에 따라 별도 인코딩하지 않음. 육아기 720만은 2배 처리로 유도. → 동의 여부 확인.

- **D-7 지급 시기/절차 (raw 170~185행).**
  3개월마다 신청, 14일 이내 지급 등은 금액이 아닌 시기/절차 → gold에서 제외(규약 7). 동의 여부 확인.

## 평가 하네스 한계 (자동 채점 전 처리 필요)

- **support_item_id 매칭**: gold는 의미 있는 안정 id(`SI-REMOTE-TELEWORK` 등)를 쓰나 LLM 후보는 `SI-001` 식 임의 id를 씀 → 내용(calculation_type+금액) 기반 정렬·매칭 어댑터 필요.
- **evidence 비교**: 규약 8에 따라 항목별 `evidence_snippets`는 생략.
