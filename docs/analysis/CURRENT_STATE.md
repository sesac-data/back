# Incentdoc v2 Current State

## 1. 현재 기술 스택

- Python/Streamlit 기반 기존 앱: `match_agent_v0.8/match_agent_v0.8/app.py`
- 정책/추천 처리: Python 서비스 모듈, OpenAI API, pandas, requests, BeautifulSoup, PyMuPDF, Pillow
- 데이터 저장: PostgreSQL을 전제로 한 SQLAlchemy 모델과 CRUD
- 프론트엔드 시안: React 19, Vite 7, lucide-react
- 정책 데이터: `data/policy_json/*.json` 정적 JSON 10개와 `incent_docs/*` 원문/메타 파일
- 테스트: pytest 스타일 단위 테스트 파일 일부 존재

## 2. 현재 디렉터리 구조

```text
project_sesac/
  product-specs/
    incentdoc-v2-user-flow-ia.md
  references/
    incentdoc-mockup-v7.html
    user-flow.png
    ia.png
  match_agent_v0.8/
    match_agent_v0.8/
      app.py
      analyzer.py
      file_parser.py
      db_builder.py
      config.py
      pages/
        upload_page.py
        confirm_page.py
        results_page.py
        form_page.py
        parental_page.py
      services/
        policy_extractor.py
        condition_evaluator.py
        calculation_service.py
        recommendation_service.py
        gap_analysis_service.py
        policy_loader_service.py
        policy_db_service.py
        recommendation_db_service.py
        ...
      database/
        db.py
        models.py
        crud.py
      data/
        policy_json/
        mock_data.py
      frontend/
        src/App.jsx
        src/styles.css
        package.json
      incent_docs/
```

## 3. 이미 구현된 기능

- Streamlit 앱에서 파일 업로드, 정보 확인, 지원금 추천, 신청서 작성, 육아휴직 관련 화면으로 이동하는 단일 흐름이 있다.
- 사업자등록증, 4대보험/인사 정보, 부가세 과세표준증명 등 일부 파일 파싱 함수가 있다.
- 정책 원문을 수집/저장하고 정책 JSON을 생성하거나 로드하는 코드가 있다.
- 정책 JSON 기반 조건 판별, 금액 계산, 중복 정책 제외, 직원별 추천 결과 생성 로직이 있다.
- PostgreSQL에 정책 버전과 추천 로그를 저장하기 위한 모델이 있다.
- React 프론트엔드는 일반기업/노무법인 역할 선택, 온보딩, 허브, 직원/고객사/서류/설정 화면을 정적 데이터로 표현한다.

## 4. 미구현 기능

- 실제 로그인, 회원가입, 계정, 권한, `user_type` 저장이 없다.
- 일반기업과 노무법인의 영속 데이터 모델이 없다.
- 회사, 노무법인, 고객사, 직원, 휴직, 제출서류, 일정, 알림, 뉴스레터, 대체인력 등 v2 운영 도메인 테이블이 없다.
- React 프론트엔드는 API 연동 없이 정적 상태와 샘플 데이터 중심이다.
- Streamlit 앱과 React 프론트엔드가 통합되어 있지 않다.
- 온보딩 Wizard가 실제 저장/재진입/스킵 상태와 연결되어 있지 않다.
- 목업의 서류 검수, 수정 요청, 승인/접수, 뉴스레터 발송, 파트너 설정, 기업 설정은 실제 기능이 아니다.

## 5. 목업과 실제 코드의 차이

- 목업은 v2 제품 IA를 보여주며 일반기업과 노무법인이 로그인 이후 완전히 다른 운영 메뉴를 가진다.
- 실제 Streamlit 앱은 기존 "지원금 추천 시스템"에 가깝고, 사용자 유형 분기 없이 업로드에서 추천까지 단일 업무 흐름이다.
- React 앱은 v2 화면 구성을 일부 반영하지만 정적 목업 수준이며 서버/DB/추천 엔진과 연결되어 있지 않다.
- 목업의 허브는 운영 현황을 요약하지만, 실제 코드는 추천 결과나 샘플 배열을 화면에 보여주는 수준이다.

## 6. 일반기업과 노무법인 플로우 분리 여부

- React 프론트엔드에서는 `role` 상태로 `company`와 `firm` 화면 메뉴를 분기한다.
- Streamlit 앱과 DB 모델에서는 일반기업/노무법인 플로우가 분리되어 있지 않다.
- 영속 계정 모델의 `user_type` 또는 `general_company`, `labor_partner` 값은 아직 없다.
- 따라서 제품 관점의 분리는 "프론트 목업 일부"에만 있고, 실제 기능/데이터/권한 분리는 미구현이다.

## 7. 핵심 엔진 구현 상태

- 정책 문서 추출: `policy_extractor.py`가 OpenAI API로 원문을 정책 JSON schema로 추출하고 파일로 저장한다. 다만 운영 파이프라인, 재검수, 버전 승인 흐름은 부족하다.
- 조건 판별: `condition_evaluator.py`가 일부 condition type을 판별한다. 정책 JSON에는 evaluator가 모르는 type도 있어 판별 누락 위험이 있다.
- 지원금 계산: `calculation_service.py`가 월액, 기간, 연 한도 기반 계산을 수행한다. 실제 신청 가능 기간, 부분 기간, 인원 한도, 회사 단위 한도는 제한적이다.
- 조합 추천: `recommendation_service.py`가 정책 충돌 규칙과 금액 기준 정렬로 직원별 추천을 만든다. 조합 최적화라기보다는 단순 선택/필터링에 가깝다.

## 8. 가장 위험한 부분

- v2의 사용자/회사/고객사/직원 도메인 모델이 없는 상태에서 화면부터 확장하면 데이터 소유권과 권한 모델을 나중에 갈아엎을 가능성이 크다.
- 정책 JSON condition type과 evaluator 지원 범위가 불일치하면 추천 결과가 조용히 빠지거나 잘못 계산될 수 있다.
- Streamlit 기존 앱, React 목업, 정책 엔진, PostgreSQL 모델이 서로 다른 방향으로 존재해 "어느 앱이 실제 제품인가"가 불명확하다.
- `database/db.py`에 로컬 PostgreSQL 접속 정보가 하드코딩되어 있어 환경 이식성과 보안 위험이 있다.

## 9. 의존성을 고려한 구현 순서

1. 제품 기준 앱 표면 결정: Streamlit 유지, React 전환, 또는 단계적 병행 여부를 확정한다.
2. 공통 도메인 모델 정의: 사용자, 사용자 유형, 일반기업, 노무법인, 고객사, 직원, 휴직/지원 이벤트를 먼저 잡는다.
3. 일반기업/노무법인 권한과 데이터 소유 경계를 DB/API 레벨에서 분리한다.
4. 온보딩 Wizard 저장 흐름을 만든다.
5. 직원/휴직 정보 관리 화면을 실제 데이터와 연결한다.
6. 정책 엔진 입력 데이터를 v2 도메인 모델에서 생성한다.
7. 추천, 서류/일정, 대체인력, 뉴스레터 순으로 운영 기능을 붙인다.

## 10. 첫 번째로 구현해야 할 최소 기능

가장 먼저 구현해야 할 최소 기능은 `user_type`을 가진 계정과 그에 연결되는 기본 조직 컨텍스트를 저장하는 것이다.

- 일반기업: 계정 -> 회사 -> 직원
- 노무법인: 계정 -> 노무법인 -> 고객사 -> 직원

이 최소 모델이 있어야 온보딩, 허브, 직원 관리, 정책 추천 결과가 같은 데이터 소유 구조 위에서 이어질 수 있다.
