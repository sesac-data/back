# 채용 지원금 추천 시스템

## 프로젝트 구조

```
subsidy_app/
├── app.py              # Streamlit 메인 앱 (UI + 라우팅)
├── config.py           # 지원금 DB 설정 (1-1 ~ 1-5)
├── db_builder.py       # DB 구축: 크롤링 + 파일 로드 (1-3, 1-4)
├── file_parser.py      # 사용자 파일 파싱: OCR + XLSX (2-1, 2-2)
├── analyzer.py         # GPT 분석: 자격 비교 + 추천 (3, 4단계)
├── requirements.txt
├── .env                # API 키 (직접 입력 필요)
└── incent_docs/
    ├── youth_hire_incent_docs/       # ← 수동으로 PDF/TXT 파일 넣기
    ├── employ_promo_incent_docs/     # ← 크롤링으로 자동 생성
    ├── perm_conv_incent_docs/        # ← 크롤링으로 자동 생성
    └── elders_employ_incent_docs/    # ← 크롤링으로 자동 생성
```

---

## 명시해야 할 부분 (직접 입력 필요)

### 1. `.env` 파일에 API 키 입력

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
```

> OCR은 EasyOCR(로컬, 무료)이므로 API 키 없이 동작합니다.
> OPENAI_API_KEY는 지원금 분석(analyzer.py)에만 사용됩니다.

### 1-1. GPU 설정 (선택)

`file_parser.py` 상단 `_get_reader()` 함수:
```python
_reader = easyocr.Reader(["ko", "en"], gpu=False)  # GPU 있으면 True
```
EasyOCR 최초 실행 시 모델 파일(약 200MB)을 자동 다운로드합니다.

### 2. `youth_hire_incent_docs/` 폴더에 수동으로 파일 넣기

`config.py`의 `incent_urls`에서 `youth_hire_incent`의 URL이 `"none"`이므로
크롤링이 수행되지 않습니다.

**직접 준비해야 할 파일:**
- 고용노동부 공식 사이트 또는 고용24에서 "청년 일자리도약 장려금" 자격 요건 PDF 다운로드
- 파일을 `incent_docs/youth_hire_incent_docs/` 폴더에 저장 (PDF, TXT 모두 가능)

**권장 파일 다운로드 경로:**
- https://www.work24.go.kr (고용24 → 사업주 지원 → 청년 일자리도약 장려금)

### 3. GPT 모델명

`analyzer.py` 상단의 `MODEL` 변수:
```python
MODEL = "gpt-4.1"   # gpt-5.4 출시 후 이 줄을 교체
```

현재 OpenAI API에 `gpt-5.4`가 미출시 상태이므로 `gpt-4.1`을 사용합니다.
출시 후 한 줄만 변경하면 됩니다.

---

## 설치 및 실행

```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. .env 파일에 API 키 입력
echo "OPENAI_API_KEY=sk-xxxx" > .env

# 3. youth_hire_incent_docs 폴더에 파일 수동 배치

# 4. 앱 실행
streamlit run app.py
```

---

## 동작 흐름

```
앱 시작
  └─ ensure_db()
       ├─ youth_hire_incent      → URL 없음 → incent_docs 폴더 파일 사용
       ├─ employ_promo_incent    → URL 크롤링 → raw.txt + meta.json 저장
       ├─ perm_conv_incent       → URL 크롤링 → raw.txt + meta.json 저장
       └─ elders_employ_incent   → URL 크롤링 → raw.txt + meta.json 저장

Step 1: 파일 업로드
  ├─ 사업자등록증  → GPT-4o Vision OCR → dict
  ├─ 4대보험 명단  → pandas 파싱 → dict (피보험자 수, 연령 분포)
  └─ 인사정보      → pandas 파싱 → dict (고용형태, 청년/고령자 수)

Step 2: 파싱 결과 확인

Step 3: 지원금 분석 (gpt-4.1 / gpt-5.4)
  └─ 지원금 DB 텍스트 + 사업주 정보 + 제출 서류 목록 → GPT 분석
       → status: eligible / conditional / ineligible
       → eligibility_checklist  (자격 요건 체크리스트)
       → extra_conditions       (추가 확인 조건 + 확인 방법)
       → extra_docs             (추가 제출 서류 + 발급처)
```

---

## DB 저장 형식 (1-4)

크롤링 결과는 두 파일로 저장됩니다:

| 파일 | 용도 |
|------|------|
| `{key}_raw.txt` | 크롤링 원문 텍스트 (GPT 컨텍스트에 직접 사용) |
| `{key}_meta.json` | 수집일, URL, 원문 텍스트 포함 메타 파일 |

JSON을 기본 저장 형식으로 추천하는 이유:
- 수집일 기록 → 정보 갱신 주기 관리 가능
- content 필드에 원문 보존 → PDF 없이도 텍스트 재사용 가능
- 향후 버전 관리 및 구조화 확장 용이
