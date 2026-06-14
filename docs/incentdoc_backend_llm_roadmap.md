# Incentdoc 백엔드 기능 개발 로드맵

## 0. 목적

이 문서는 Incentdoc 프로젝트의 백엔드 기능 개발을 중간 확인 없이 단계별로 이어서 진행하기 위한 실행 계획이다.

현재 프론트엔드는 별도 담당자가 진행 중이므로, 기존 API 응답 계약을 유지하고 백엔드 기능 개발과 자동 검증에 집중한다.

최종 목표는 아래 흐름을 안정적으로 완성하는 것이다.

```text
공식 정책 페이지·문서
→ db_builder 수집
→ 원문 로드
→ LLM 구조화 후보 생성
→ 후보 조립
→ Schema Validation Gate
→ needs_review 후보 저장
→ 사람 검토
→ approved 정책 반영
→ 코드 기반 추천 엔진
→ 최적 지원금 조합 반환
```

---

# 1. 현재 완료된 상태

## 1.1 추천 계산 엔진

아래 기능은 구현 및 자동 검증이 완료된 상태다.

```text
approved 정책만 계산 진입
→ 조건 판별
→ monthly_fixed 계산
→ period_tiered 계산
→ conditional_bonus 계산
→ 정책별 결과 표준화
→ mutually_exclusive 충돌 감지
→ requires 선행 정책 검증
→ 유효 조합 생성
→ 조합별 총지원금 합산
→ 사업주 순비용 계산
→ 순비용 기준 최적 조합 선택
```

## 1.2 정책 DB 연결

Supabase PostgreSQL의 `subsidy_policies` 테이블을 사용한다.

```text
policy_source = demo_fixture
→ 기존 fixture 정책 사용

policy_source = policy_db
→ Supabase subsidy_policies 조회
→ review_status = approved
→ is_active = true
→ 조건을 만족하는 정책만 추천 엔진에 전달
```

## 1.3 FastAPI 서버

아래 HTTP 계층이 구현되어 있다.

```text
GET  /health
POST /api/demo/recommendations/calculate
```

실행 예시:

```powershell
cd C:\Users\laiep\project_sesac\match_agent_v0.8\match_agent_v0.8
python -m uvicorn api_server:app --host 127.0.0.1 --port 8000 --env-file ".env"
```

## 1.4 LLM 정책 구조화 평가 하네스

아래 기능이 구현되어 있다.

```text
정책 원문 fixture
→ OpenAI adapter
→ JSON 후보 생성
→ gold JSON 비교
→ 점수 계산
→ 오류 유형 집계
→ JSON / Markdown 리포트 생성
```

`policy_extraction_v2` 기준 5회 반복 평가 결과:

```text
평균: 79.15
최저: 77.21
최고: 80.89
```

## 1.5 db_builder 연동

기존 `db_builder.py`가 수집한 정책 문서를 LLM 추출기에 연결했다.

기존 저장 구조:

```text
config.py
→ INCENT_DOCS_ROOT = match_agent_v0.8/match_agent_v0.8/incent_docs

incent_docs/{incent_key}_docs/
├── {incent_key}_raw.txt
├── {incent_key}_meta.json
├── *.pdf
├── *.txt
├── *.json
└── *.docx
```

지원 입력 형식:

```text
.txt
.md
.json
.pdf
.docx
```

미지원:

```text
legacy .doc 바이너리 Word 문서
```

## 1.6 실제 문서 추출 결과

`childcare_flexible_start_support` 문서를 대상으로 `policy_extraction_v3`를 실행했다.

개선된 항목:

```text
- 6개월 이상 기간 조건 분리
- 주 35시간 이상 조건 분리
- 30시간 초과 / 35시간 이하 범위 분리
- 매일 1시간 단축 조건 추출
- 임금 삭감 금지 추출
- 취업규칙 규정 추출
- 전자·기계적 근태관리 추출
- Q&A 중복 수급 제한 후보 추출
- 복합 인원 한도를 unresolved_rules로 분리
```

현재 Validator에서 검출된 오류:

```text
missing_policy_id
missing_calculation_type
evidence_not_in_raw_text
unknown_policy_id
```

---

# 2. 공통 작업 원칙

모든 단계에서 아래 원칙을 지킨다.

## 2.1 반드시 먼저 읽을 파일

```text
AGENTS.md
model_설명.txt
docs/ARCHITECTURE.md
docs/POLICY_SCHEMA.md
docs/RULE_ENGINE.md
docs/RECOMMENDATION_RULES.md
docs/TEST_SCENARIOS.md
docs/DEVELOPMENT_SETUP.md
tasks/feature_list.json
tasks/progress.md
```

## 2.2 변경 금지 영역

특정 단계에서 명시적으로 허용하지 않는 한 아래 영역은 변경하지 않는다.

```text
frontend/
analyzer.py
file_parser.py
mapping.py
writer_final.py
기존 추천 API 응답 계약
기존 계산 산식
기존 DB Schema
기존 테스트 삭제 또는 완화
```

## 2.3 LLM 사용 원칙

```text
- LLM 후보는 항상 review_status = needs_review
- LLM 후보를 자동 approved 처리하지 않음
- LLM 결과를 자동 보정하지 않음
- 의미 필드를 코드로 임의 변환하지 않음
- 원문에 없는 값을 추론하지 않음
- 모든 조건·금액·규칙은 evidence_snippets를 포함
- evidence_snippets는 원문 substring을 유지
```

## 2.4 검증 원칙

각 단계 종료 시 반드시 실행한다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode full
git diff --check
```

필요하면 추가로 실행한다.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify.ps1 -Mode demo
python scripts\run_recommendation_acceptance.py
```

## 2.5 자동 진행 중단 조건

아래 상황에서는 다음 단계로 자동 진행하지 말고, 문제와 필요한 의사결정만 보고한다.

```text
- 기존 테스트 실패
- full 검증 실패
- DB migration 충돌
- 기존 API 응답 계약 변경 필요
- Schema 변경 없이 표현 불가능한 정책 규칙 발견
- 운영 DB 접근 필요
- 실제 정책 ID 매핑 기준이 불명확함
- 보안 정보 또는 API Key가 로그에 노출됨
```

---

# 3. 단계별 실행 계획

## Stage 1. 후보 조립 계층 추가 및 v4 프롬프트 작성

### 목표

LLM이 해석해야 하는 값과 시스템이 보유한 메타데이터를 분리한다.

```text
LLM raw candidate
→ candidate assembler
→ assembled candidate
→ validator
```

### 구현 항목

```text
- db_builder metadata의 incent_key를 policy_id로 주입
- source_document_id, source_url, source_file을 코드에서 연결
- LLM raw candidate와 assembled candidate를 분리 저장
- validator는 assembled candidate를 검증
- evidence 검증 시 공백·개행만 정규화하여 substring 비교
- 원본 evidence_snippets 값은 변경하지 않음
- prompts/policy_extraction_v4.md 추가
```

### v4 프롬프트 강화 규칙

```text
- support_items에는 calculation_type 필수
- calculation_type 허용 값:
  monthly_fixed, period_tiered, conditional_bonus
- support_type, monthly_amount 같은 alias를 calculation_type 대신 사용 금지
- support_items 중복 출력 금지
- 대상 policy_id가 불명확하면 UNKNOWN_POLICY_ID를 쓰지 않음
- 불명확한 중복 수급 규칙은 unresolved_rules로 이동
- unresolved_rules는 parsed_candidate와 별도 배열로 유지
- 원문에 없는 값 추론 금지
- review_status는 needs_review 유지
```

### 권장 파일

```text
services/policy_extraction_candidate_assembler.py
test_policy_extraction_candidate_assembler.py
prompts/policy_extraction_v4.md
scripts/run_policy_extraction_from_db_builder.py
```

### 검증

```text
- incent_key 기반 policy_id 주입
- source metadata 연결
- raw candidate 불변성
- assembled candidate 별도 생성
- evidence 공백·개행 정규화 비교
- UNKNOWN_POLICY_ID 차단 유지
- calculation_type 누락 차단 유지
- 기존 v3 후보 회귀 검증
- full 검증
- git diff --check
```

### 완료 조건

아래 오류가 사라져야 한다.

```text
missing_policy_id
evidence_not_in_raw_text
```

아래 오류는 프롬프트 개선으로 사라져야 한다.

```text
missing_calculation_type
unknown_policy_id
```

### 실행 예시

```powershell
python scripts\run_policy_extraction_from_db_builder.py `
  --document-id childcare_flexible_start_support `
  --prompt-path prompts\policy_extraction_v4.md `
  --prompt-version policy_extraction_v4
```

---

## Stage 2. unresolved_rules 표준화

### 목표

현재 Schema로 표현하지 못하는 규칙을 임의로 누락하지 않고 별도 구조로 저장한다.

### 최소 유형

```text
unsupported_or_condition
ambiguous_target_policy
complex_headcount_cap
shared_duration_cap
ambiguous_time_unit
monthly_exclusion_rule
unsupported_combination_rule
schema_gap
```

### 출력 예시

```json
{
  "parsed_candidate": {},
  "unresolved_rules": [
    {
      "rule_id": "UR-001",
      "rule_type": "complex_headcount_cap",
      "description": "전년도 말일 고용보험 피보험자 수의 30%, 최소 3명, 최대 30명",
      "evidence_snippets": ["원문 구간"]
    }
  ]
}
```

### 구현 항목

```text
- unresolved_rules validator 추가
- rule_id 중복 차단
- rule_type 허용 목록 검증
- description 필수
- evidence_snippets 필수
- 원문 substring 검증
- 유형별 집계 리포트 추가
```

### 권장 파일

```text
services/unresolved_rule_validator.py
test_unresolved_rule_validator.py
scripts/run_policy_extraction_from_db_builder.py
```

### 완료 조건

```text
- UNKNOWN_POLICY_ID가 combination_rules에 들어가지 않음
- 불명확한 대상 정책은 ambiguous_target_policy로 분리
- 복합 인원 한도는 complex_headcount_cap으로 분리
- 해당 월 부지급 조건은 monthly_exclusion_rule로 분리
```

---

## Stage 3. db_builder 문서 일괄 추출 Runner

### 목표

`incent_docs` 전체 문서를 순회하여 구조화 후보와 오류 리포트를 생성한다.

### 구현 항목

```text
- 전체 문서 탐색
- 문서별 LLM 추출
- 문서별 assembled candidate 생성
- validator 실행
- 성공 / 실패 / unresolved 집계
- run_id별 출력 디렉터리 저장
- 재실행 시 기존 출력 덮어쓰기 금지
- --document-id 단일 실행 유지
- --all 전체 실행 추가
```

### 출력 구조

```text
output/policy_extraction_from_db_builder/{run_id}/
├── candidates/
│   ├── {document_id}.json
│   └── ...
├── summary-report.json
└── summary-report.md
```

### 리포트 최소 항목

```text
- 전체 문서 수
- 성공 문서 수
- validator 실패 문서 수
- parse_error 문서 수
- unresolved_rules 유형별 수
- 문서별 오류 목록
- 모델명
- 프롬프트 버전
- prompt_sha256
- 토큰 사용량 합계
- 총 실행 시간
```

### 완료 조건

```text
- 실제 문서 3개 이상 일괄 추출
- 문서별 후보 저장
- 오류 리포트 생성
- 실패 문서가 있어도 전체 실행은 중단하지 않고 집계
```

---

## Stage 4. 실제 문서 3~5개 기준 품질 분석

### 목표

Mock fixture가 아니라 실제 `db_builder` 문서에서 반복적으로 발생하는 오류를 파악한다.

### 실행 항목

```text
- childcare_flexible_start_support
- 육아휴직 관련 정책 문서
- 육아기 근로시간 단축 관련 정책 문서
- 대체인력 지원 관련 정책 문서
- 업무분담 지원 관련 정책 문서
```

### 분석 항목

```text
- missing_condition
- operator_mismatch
- amount_mismatch
- duration_mismatch
- missing_evidence
- evidence_not_in_raw_text
- ambiguous_target_policy
- complex_headcount_cap
- monthly_exclusion_rule
- unsupported_or_condition
```

### 완료 조건

```text
- 실제 문서별 오류 유형 정리
- 반복 등장하는 Schema gap 집계
- 다음 Rule Engine 확장 우선순위 결정
```

### 주의

이 단계에서는 정답 fixture가 없을 수 있다.

따라서 자동 점수보다 아래를 우선한다.

```text
- validator 통과 여부
- unresolved_rules 적절성
- evidence 연결 여부
- 사람이 검토 가능한 수준인지
```

---

## Stage 5. needs_review 후보 저장 테이블 추가

### 목표

검증을 통과한 LLM 후보를 승인 전 상태로 Supabase에 저장한다.

### 신규 테이블

```text
policy_extraction_candidates
```

### 권장 컬럼

```sql
id BIGSERIAL PRIMARY KEY,
candidate_id VARCHAR(150) NOT NULL UNIQUE,
policy_id VARCHAR(150) NOT NULL,
source_document_id VARCHAR(255) NOT NULL,
source_url TEXT,
source_file TEXT NOT NULL,
model VARCHAR(100) NOT NULL,
prompt_version VARCHAR(100) NOT NULL,
prompt_sha256 VARCHAR(64) NOT NULL,
review_status VARCHAR(30) NOT NULL DEFAULT 'needs_review',
candidate_json JSONB NOT NULL,
unresolved_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
validation_errors JSONB NOT NULL DEFAULT '[]'::jsonb,
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

### review_status 허용 값

```text
needs_review
approved
rejected
```

### 구현 항목

```text
- migration SQL 추가
- repository 추가
- 저장 스크립트 추가
- 동일 candidate_id 중복 방지
- validator 실패 후보 저장 정책 명확화
```

### 저장 정책

권장:

```text
validator 통과
→ needs_review 저장 가능

validator 실패
→ 저장 금지
→ 로컬 리포트에만 기록

unresolved_rules 존재
→ needs_review 저장 가능
→ 사람이 검토해야 함
```

### 완료 조건

```text
- validator 통과 후보 저장
- validator 실패 후보 저장 차단
- unresolved_rules 포함 후보 저장 가능
- subsidy_policies에는 자동 반영하지 않음
```

---

## Stage 6. 승인 처리 백엔드 로직

### 목표

사람 검토가 완료된 후보만 승인 정책으로 반영한다.

### 흐름

```text
policy_extraction_candidates
→ 사람이 검토
→ approve command
→ subsidy_policies upsert
→ approved_policy_loader 사용 가능
```

### 구현 항목

```text
- approve candidate service
- reject candidate service
- 승인 전 validator 재실행
- unresolved_rules가 남아 있으면 승인 차단 또는 명시적 override 필요
- 승인 이력 저장
- 원본 candidate_json 보존
- approved JSON 별도 생성
```

### 중요

```text
- 자동 approved 금지
- unresolved_rules가 남은 후보 자동 승인 금지
- 기존 승인 정책을 덮어쓸 때 policy_version 필요
- 승인 시 source_document_id 추적 유지
```

### 완료 조건

```text
- needs_review → approved 전환
- approved 정책 subsidy_policies 저장
- rejected 후보 분리
- 추천 엔진은 approved 정책만 사용
```

---

## Stage 7. 정책 ID 및 대상 정책 매핑 사전

### 목표

LLM이 정책 이름을 추출했지만 시스템 `policy_id`를 모르는 경우 안정적으로 매핑한다.

### 예시

```text
육아기 근로시간 단축 제도
→ childcare_working_hour_reduction_support

워라밸일자리장려금 소정근로시간 단축
→ worklife_reduced_hours_support
```

### 구현 항목

```text
- 정책 alias 사전
- alias → policy_id resolver
- exact match 우선
- normalized alias match
- ambiguous match는 unresolved_rules 유지
- 임의 추론 금지
```

### 권장 파일

```text
services/policy_alias_resolver.py
test_policy_alias_resolver.py
data/policy_aliases.json
```

### 완료 조건

```text
- 명확한 대상 정책 이름은 policy_id로 변환
- 애매한 이름은 ambiguous_target_policy 유지
- UNKNOWN_POLICY_ID 사용 금지
```

---

## Stage 8. Rule Engine 확장 우선순위

실제 문서 분석 결과에 따라 아래 기능을 순차 구현한다.

### 8.1 OR 조건

예:

```text
만 12세 이하 또는 초등학교 6학년 이하
```

권장 구조:

```json
{
  "condition_group_id": "CG-001",
  "mode": "or",
  "conditions": []
}
```

### 8.2 shared_duration_cap

예:

```text
기존 워라밸일자리장려금과 사용기간을 합산하여 최대 1년
```

### 8.3 complex_headcount_cap

예:

```text
피보험자 수의 30%
10명 미만이면 3명
최대 30명
```

### 8.4 monthly_exclusion_rule

예:

```text
출퇴근기록 누락일수가 월 3일 초과 시 해당 월 부지급
연장근로 월 10시간 초과 시 해당 월 부지급
```

### 8.5 정책별 한도 및 기업 단위 한도

```text
직원 단위 계산
→ 기업 단위 인원 한도 검증
→ 최종 지원금 조정
```

### 진행 원칙

```text
실제 문서에서 반복 등장한 유형부터 구현
한 번에 하나의 Rule Engine 기능만 추가
기능마다 단위 테스트 + acceptance 추가
```

---

## Stage 9. 실제 정책 기반 추천 Acceptance

### 목표

Fixture가 아닌 승인된 실제 정책 JSON으로 추천 엔진을 검증한다.

### 시나리오

```text
- 조건 충족 일반 기업
- 조건 미충족 기업
- 30시간 초과 / 35시간 이하 경계값
- 6개월 미만 / 이상 경계값
- 월별 부지급 조건
- 중복 정책 동시 신청
- 기간 합산 상한
- 기업 인원 한도
```

### 완료 조건

```text
- 실제 승인 정책 3개 이상
- acceptance 자동 실행
- calculation_steps 및 evidence 확인
- 잘못된 정책 추천 없음
```

---

## Stage 10. 운영 실행 스크립트 통합

### 목표

백엔드 파이프라인을 하나의 실행 흐름으로 연결한다.

### 권장 흐름

```text
python scripts/run_policy_pipeline.py --all
```

### 내부 단계

```text
1. db_builder 실행 또는 기존 문서 확인
2. 신규·변경 문서 감지
3. LLM 후보 생성
4. assembler 실행
5. validator 실행
6. unresolved_rules 집계
7. needs_review 후보 저장
8. 리포트 생성
```

### 중요

```text
- 자동 승인 금지
- subsidy_policies 자동 반영 금지
- 변경 문서만 재처리
- content_hash 기반 중복 방지
- 실패 문서 재시도 가능
```

---

## Stage 11. 관측성 및 리포트

### 목표

기능이 많아져도 실패 지점을 바로 확인할 수 있게 한다.

### 리포트 항목

```text
- 수집 문서 수
- 신규 문서 수
- 변경 문서 수
- LLM 추출 성공 수
- parse_error 수
- validator 실패 수
- unresolved_rules 유형별 수
- needs_review 저장 수
- 승인 수
- 모델명
- 프롬프트 버전
- token_usage 합계
- 문서별 elapsed_ms
```

### 출력

```text
output/policy_pipeline/{run_id}/summary-report.json
output/policy_pipeline/{run_id}/summary-report.md
```

---

## Stage 12. 안정화 및 정리

### 목표

백엔드 기능을 운영 가능한 수준으로 정리한다.

### 점검 항목

```text
- .env 자동 로드 방식 통일
- API Key 로그 노출 방지
- DB URL 로그 노출 방지
- migration 순서 정리
- seed 분리
- 개발용 fixture와 실제 정책 분리
- README 업데이트
- full 검증 실행
- demo 검증 실행
- git diff --check
```

---

# 4. Codex에 전달할 연속 실행 지시문

아래 내용을 Codex에 전달하면 된다.

```text
AGENTS.md, model_설명.txt, docs 전체, tasks/feature_list.json,
tasks/progress.md를 먼저 읽어.

incentdoc_backend_llm_roadmap.md를 기준으로 Stage 1부터 순서대로 진행해.

진행 규칙:
1. 한 번에 Stage 하나만 구현해.
2. 각 Stage 종료 후 반드시 단위 테스트, full 검증, git diff --check를 실행해.
3. 검증이 통과하면 tasks/feature_list.json과 tasks/progress.md를 업데이트해.
4. 검증이 통과하면 다음 Stage로 진행해.
5. 기존 테스트 실패, DB migration 충돌, API 계약 변경 필요,
   Schema 의사결정 필요, 운영 DB 접근 필요 상황에서는 즉시 멈추고 보고해.
6. 프론트는 변경하지 마.
7. analyzer.py, file_parser.py, mapping.py, writer_final.py는 변경하지 마.
8. 자동 approved 처리 금지.
9. subsidy_policies 자동 저장 금지.
10. LLM 후보 자동 보정 금지.
11. 의미 필드를 코드로 임의 변환하지 마.
12. 원문에 없는 값을 추론하지 마.
13. API Key, DB URL, 비밀번호를 로그에 출력하지 마.
14. 기존 파일과 폴더는 삭제하지 마.

각 Stage 완료 후 아래 형식으로 progress.md에 기록해.
- Stage 번호와 이름
- 수정 파일
- 구현 내용
- 재사용한 기존 코드
- 테스트 결과
- full 검증 결과
- git diff --check 결과
- 남은 문제
- 다음 Stage 진행 가능 여부

가능하면 Stage 1부터 Stage 4까지 연속으로 진행해.
Stage 5부터는 Supabase migration이 필요하므로 migration SQL을 추가한 뒤 멈추고 보고해.
```

---

# 5. 권장 자동 진행 범위

한 번에 모두 진행시키기보다 아래처럼 끊는 것을 권장한다.

## 1차 자동 진행

```text
Stage 1
→ Stage 2
→ Stage 3
→ Stage 4
```

목적:

```text
LLM 구조화 품질 개선
→ 실제 문서 일괄 추출
→ 오류 유형 집계
→ Rule Engine 확장 우선순위 확정
```

## 2차 자동 진행

```text
Stage 5
→ Stage 6
→ Stage 7
```

목적:

```text
needs_review 저장
→ 승인 처리
→ 정책 ID 매핑
```

## 3차 자동 진행

```text
Stage 8
→ Stage 9
```

목적:

```text
실제 정책에서 반복 등장한 규칙 구현
→ 실제 정책 기반 추천 Acceptance
```

## 4차 자동 진행

```text
Stage 10
→ Stage 11
→ Stage 12
```

목적:

```text
운영 파이프라인 통합
→ 리포트
→ 안정화
```

---

# 6. 다음 즉시 실행할 범위

현재는 아래를 바로 실행한다.

```text
Stage 1. 후보 조립 계층 추가 및 v4 프롬프트 작성
→ Stage 2. unresolved_rules 표준화
→ Stage 3. db_builder 문서 일괄 추출 Runner
→ Stage 4. 실제 문서 3~5개 기준 품질 분석
```

Stage 5의 Supabase migration은 SQL 파일만 준비하고, 실제 적용 전에는 멈춰서 보고한다.
