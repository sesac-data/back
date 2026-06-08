"""
file_parser.py
사용자 업로드 파일 파싱 모듈 (2-1, 2-2)

담당:
  - 사업자등록증(PDF/이미지)        → GPT-4o Vision OCR → dict
  - 인사정보(제출).xlsx             → pandas DataFrame → dict
  - 부가가치세 과세표준증명.pdf      → PyMuPDF 텍스트 추출 + GPT 구조화 → dict
"""

import base64
import io
import json
import os
import re
import datetime
from pathlib import Path

import fitz
import pandas as pd
from openai import OpenAI
from PIL import Image

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# ─────────────────────────────────────────────
# 내부 유틸: 파일 → base64 PNG
# ─────────────────────────────────────────────

def _to_base64_png(file_bytes: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pix = doc[0].get_pixmap(dpi=200)
        img_bytes = pix.tobytes("png")
    else:
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()
    return base64.b64encode(img_bytes).decode("utf-8")


# ─────────────────────────────────────────────
# 내부 유틸: 동적 헤더 행 탐지
# ─────────────────────────────────────────────

def _find_header_row(file_bytes: bytes, anchor_keywords: list) -> int:
    """anchor_keywords 중 하나라도 포함된 행을 헤더 행으로 탐지. 못 찾으면 0 반환."""
    raw = pd.read_excel(io.BytesIO(file_bytes), dtype=str, header=None)
    for i, row in raw.iterrows():
        row_vals = row.dropna().astype(str).tolist()
        for kw in anchor_keywords:
            if any(kw in v for v in row_vals):
                return int(i)
    return 0


def _load_excel_smart(file_bytes: bytes, anchor_keywords: list) -> pd.DataFrame:
    """헤더 행을 자동 탐지하여 DataFrame 반환."""
    header_row = _find_header_row(file_bytes, anchor_keywords)
    df = pd.read_excel(io.BytesIO(file_bytes), dtype=str, header=header_row)
    df.columns = df.columns.str.strip()
    df = df.dropna(how="all").reset_index(drop=True)
    return df


# ─────────────────────────────────────────────
# 2-2. 사업자등록증 OCR (GPT-4o Vision)
# ─────────────────────────────────────────────

BIZ_OCR_PROMPT = """
다음 사업자등록증 이미지에서 아래 항목을 추출하여 JSON으로만 반환하세요.
JSON 외 다른 텍스트, 마크다운 코드블록은 절대 포함하지 마세요.

추출 항목:
- company_name      : 상호 (법인명 또는 상호)
- business_reg_no   : 사업자등록번호 (000-00-00000 형식)
- ceo_name          : 대표자 성명
- business_type     : 업태
- business_item     : 종목
- address           : 사업장 소재지
- open_date         : 개업 연월일 (YYYY-MM-DD)
- corp_reg_no       : 법인등록번호 (없으면 null)

값을 확인할 수 없는 항목은 null로 표기하세요.
"""


def parse_biz_registration(file_bytes: bytes, filename: str) -> dict:
    b64 = _to_base64_png(file_bytes, filename)
    response = client.chat.completions.create(
        model="gpt-4o",
        max_completion_tokens=800,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"}},
                {"type": "text", "text": BIZ_OCR_PROMPT},
            ],
        }],
    )
    raw = response.choices[0].message.content.strip()
    try:
        return json.loads(raw.replace("```json", "").replace("```", "").strip())
    except json.JSONDecodeError:
        return {"parse_error": raw}


# ─────────────────────────────────────────────
# 부가가치세 과세표준증명 파싱
# ─────────────────────────────────────────────

VAT_PARSE_PROMPT = """
아래는 부가가치세 과세표준증명 문서에서 추출한 텍스트입니다.
다음 항목을 추출하여 JSON으로만 반환하세요.
JSON 외 다른 텍스트, 마크다운 코드블록은 절대 포함하지 마세요.

추출 항목:
- business_reg_no : 사업자등록번호 (000-00-00000 형식)
- company_name    : 상호(법인명)
- annual_sales    : 과세기간별 매출과세표준 목록 (아래 형식)
  [
    {{"year": 2024, "period_start": "2024-01-01", "period_end": "2024-12-31", "amount": 220000000}},
    ...
  ]
  - amount는 숫자(원 단위, 콤마 없음)
  - 1년 미만 과세기간도 그대로 포함

[날짜 추출 주의사항]
- 문서에는 "부터"에 해당하는 날짜와 "까지"에 해당하는 날짜가 순서대로 나열됩니다.
- 각 행의 "부터" 날짜가 period_start, "까지" 날짜가 period_end입니다.
- period_start는 반드시 period_end보다 이전 날짜여야 합니다.
- year는 period_start의 연도를 기준으로 합니다.
- 날짜가 뒤바뀌지 않도록 반드시 start < end 를 확인하세요.

- best_year_sales  : annual_sales 중 가장 높은 amount 값 (숫자)
- best_year        : best_year_sales에 해당하는 year (숫자)

값을 확인할 수 없는 항목은 null로 표기하세요.

[문서 텍스트]
{text}
"""


def parse_vat_certificate(file_bytes: bytes) -> dict:
    """
    부가가치세 과세표준증명 PDF → 매출액 정보 dict 반환

    PyMuPDF로 텍스트 직접 추출 후 GPT로 구조화.
    텍스트 추출 실패 시 GPT-4o Vision으로 폴백.

    Returns:
        {
          "business_reg_no" : str,
          "company_name"    : str,
          "annual_sales"    : [ { "year": int, "period_start": str, "period_end": str, "amount": int }, ... ],
          "best_year_sales" : int,   # 가장 높은 연 매출액
          "best_year"       : int,   # 해당 연도
          # 오류 시:
          "parse_error"     : str,
        }
    """
    # 1. PyMuPDF로 텍스트 추출 시도
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc).strip()
    except Exception as e:
        text = ""
        print(f"[file_parser] VAT PDF 텍스트 추출 실패: {e}")

    if len(text) >= 50:
        # 텍스트 레이어 있음 → GPT 텍스트 모드
        prompt = VAT_PARSE_PROMPT.format(text=text)
        response = client.chat.completions.create(
            model="gpt-4o",
            max_completion_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
    else:
        # 텍스트 레이어 없음 → GPT Vision 폴백
        print("[file_parser] VAT PDF 텍스트 부족 → Vision 폴백")
        b64 = _to_base64_png(file_bytes, "vat.pdf")
        vision_prompt = VAT_PARSE_PROMPT.format(text="[이미지에서 직접 읽어주세요]")
        response = client.chat.completions.create(
            model="gpt-4o",
            max_completion_tokens=800,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}", "detail": "high"}},
                    {"type": "text", "text": vision_prompt},
                ],
            }],
        )

    raw = response.choices[0].message.content.strip()
    try:
        result = json.loads(raw.replace("```json", "").replace("```", "").strip())

        # 날짜 역전 자동 수정 (period_start > period_end 인 경우 swap)
        for s in result.get("annual_sales", []):
            start = s.get("period_start", "")
            end   = s.get("period_end", "")
            if start and end and start > end:
                s["period_start"], s["period_end"] = end, start
                print(f"[file_parser] VAT 날짜 역전 수정: {end} ↔ {start}")
            # year는 period_start 기준으로 재설정
            if s.get("period_start"):
                s["year"] = int(s["period_start"][:4])

        # best_year_sales가 없으면 직접 계산
        if result.get("annual_sales") and not result.get("best_year_sales"):
            full_year = [s for s in result["annual_sales"] if s.get("amount")]
            if full_year:
                best = max(full_year, key=lambda x: x["amount"])
                result["best_year_sales"] = best["amount"]
                result["best_year"] = best["year"]
        return result
    except json.JSONDecodeError:
        return {"parse_error": raw}


# ─────────────────────────────────────────────
# 인사정보 파싱
# ─────────────────────────────────────────────

def _extract_meta_fields(file_bytes: bytes) -> dict:
    """
    인사정보 파일 상단 메타 영역(헤더 이전 행)에서
    기업명, 사업자번호, 표준산업분류코드 추출
    """
    raw = pd.read_excel(io.BytesIO(file_bytes), dtype=str, header=None)
    meta = {}
    for _, row in raw.iterrows():
        row_vals = row.dropna().astype(str).tolist()
        # 헤더 행 도달 시 중단
        if any(kw in row_vals for kw in ["연번", "성명", "주민등록번호"]):
            break
        if len(row_vals) >= 2:
            key = row_vals[0].strip()
            val = row_vals[1].strip() if len(row_vals) > 1 else ""
            if "기업명" in key:
                meta["company_name"] = val
            elif "사업자번호" in key or "사업자등록번호" in key:
                meta["business_reg_no"] = val
            elif "표준산업분류" in key:
                meta["industry_code"] = val
    return meta


def parse_hr_info(file_bytes: bytes) -> dict:
    """
    인사정보(제출).xlsx → 집계 dict 반환

    집계 항목:
    - total_employees   : 성명 컬럼 유효 행 수
    - insured_count     : 고용보험 값이 있는 직원 수 (피보험자 수, 매출액 요건 기준)
    - employment_types  : 고용형태별 카운트
    - youth_count       : 15~34세 직원 수 (주민번호 기반)
    - elder_count       : 60세 이상 직원 수 (주민번호 기반)
    - youth_vulnerable_count  : 취업애로청년 Y인 직원 수
    - new_hire_count    : 신규채용 Y인 직원 수
    - owner_related_count     : 사업주관계 Y인 직원 수 (지원 제외 대상)
    - ineligible_hours_count  : 주근로시간 28시간 미만 직원 수
    - over_salary_count : 급여 450만원 초과 직원 수
    - active_employees  : 퇴사일 없는 현재 재직자 수
    """
    meta = _extract_meta_fields(file_bytes)

    df = _load_excel_smart(
        file_bytes,
        anchor_keywords=["성명", "고용형태", "입사일", "생년월일", "직위"],
    )

    # Unnamed 컬럼 제거
    df = df[[c for c in df.columns if not str(c).startswith("Unnamed")]]

    # ── 기본 카운트 ──────────────────────────
    name_col = _find_col(df, ["성명", "이름", "name"])
    total = int(df[name_col].dropna().count()) if name_col else len(df)

    # 피보험자 수: 고용보험 컬럼에 값이 있는 행
    insurance_col = _find_col(df, ["고용보험", "고용보험형태", "보험"])
    insured_count = 0
    if insurance_col:
        insured_count = int(df[insurance_col].dropna().apply(
            lambda x: str(x).strip() not in ("", "-", "nan")
        ).sum())

    # ── 고용형태 ─────────────────────────────
    emp_col = _find_col(df, ["고용형태", "근로형태", "고용구분", "직종유형", "employment_type"])
    emp_types = {}
    if emp_col:
        emp_types = df[emp_col].value_counts().to_dict()

    # ── 연령 (주민번호 기반) ─────────────────
    today = datetime.date.today()
    birth_col = _find_col(df, ["생년월일", "주민등록번호", "주민번호", "생년", "birth"])
    youth_count = 0
    elder_count = 0
    if birth_col:
        for val in df[birth_col].dropna():
            yr = _extract_birth_year(str(val))
            if yr:
                age = today.year - yr
                if 15 <= age <= 34:
                    youth_count += 1
                elif age >= 60:
                    elder_count += 1

    # ── 취업애로청년 Y 카운트 ────────────────
    vuln_col = _find_col(df, ["취업애로청년", "취약계층", "취업애로"])
    youth_vulnerable_count = 0
    if vuln_col:
        youth_vulnerable_count = int(
            df[vuln_col].apply(lambda x: str(x).strip().upper() == "Y").sum()
        )

    # ── 신규채용 Y 카운트 ────────────────────
    new_hire_col = _find_col(df, ["신규채용", "신규"])
    new_hire_count = 0
    if new_hire_col:
        new_hire_count = int(
            df[new_hire_col].apply(lambda x: str(x).strip().upper() == "Y").sum()
        )

    # ── 사업주관계 Y 카운트 (지원 제외 대상) ─
    owner_col = _find_col(df, ["사업주관계", "대표자관계", "사업주"])
    owner_related_count = 0
    if owner_col:
        owner_related_count = int(
            df[owner_col].apply(lambda x: str(x).strip().upper() == "Y").sum()
        )

    # ── 주근로시간 28시간 미만 카운트 ────────
    hours_col = _find_col(df, ["주근로시간", "주당근로시간", "근로시간"])
    ineligible_hours_count = 0
    if hours_col:
        for val in df[hours_col].dropna():
            try:
                h = float(str(val).replace("h", "").replace("시간", "").strip())
                if h < 28:
                    ineligible_hours_count += 1
            except ValueError:
                pass

    # ── 급여 450만원 초과 카운트 ─────────────
    salary_col = _find_col(df, ["급여(원)", "급여", "급여(월)", "월급여", "임금"])
    over_salary_count = 0
    if salary_col:
        for val in df[salary_col].dropna():
            try:
                s = float(str(val).replace(",", "").replace("만", "0000").replace("원", "").strip())
                if s > 4_500_000:
                    over_salary_count += 1
            except ValueError:
                pass

    # ── 현재 재직자 (퇴사일 없는 행) ─────────
    resign_col = _find_col(df, ["퇴사일", "퇴직일", "퇴직"])
    active_employees = total
    if resign_col:
        active_employees = int(
            df[resign_col].apply(
                lambda x: str(x).strip() in ("", "-", "nan", "None")
            ).sum()
        )

    return {
        "company_name":           meta.get("company_name", ""),
        "business_reg_no":        meta.get("business_reg_no", ""),
        "industry_code":          meta.get("industry_code", ""),
        "total_employees":        total,
        "insured_count":          insured_count,
        "active_employees":       active_employees,
        "employment_types":       emp_types,
        "youth_count":            youth_count,
        "elder_count":            elder_count,
        "youth_vulnerable_count": youth_vulnerable_count,
        "new_hire_count":         new_hire_count,
        "owner_related_count":    owner_related_count,
        "ineligible_hours_count": ineligible_hours_count,
        "over_salary_count":      over_salary_count,
        "raw_df_json":            df.to_json(force_ascii=False, orient="records"),
        "columns":                df.columns.tolist(),
        "records":                df.to_dict(orient="records"),
    }


# ─────────────────────────────────────────────
# 내부 헬퍼
# ─────────────────────────────────────────────

def _find_col(df: pd.DataFrame, candidates: list) -> str | None:
    """후보 컬럼명 중 DataFrame에 존재하는 첫 번째 반환"""
    for c in candidates:
        for col in df.columns:
            if c in str(col):
                return col
    return None


def _extract_birth_year(val: str) -> int | None:
    """다양한 형식에서 출생연도 추출"""
    clean = val.replace("-", "").replace(".", "").strip()

    # YYYY 형식 (생년월일: YYYY-MM-DD, YYYYMMDD 등) — 먼저 처리
    m = re.search(r"(19|20)\d{2}", val)
    if m and (val.count("-") >= 1 or len(clean) == 8):
        return int(m.group())

    # 주민번호 형식
    m = re.match(r"(\d{2})(\d{2})(\d{2})(\d{7})?", clean)
    if m and len(clean) >= 7:
        yy = int(m.group(1))
        back = clean[6:7]
        if back in ("1", "2"):
            return 1900 + yy
        elif back in ("3", "4"):
            return 2000 + yy

    return None
