"""
analyzer.py
GPT 기반 지원금 자격 분석 모듈 (3-1, 3-2, 4-1, 4-2)
"""

import json
import os

from openai import OpenAI

from config import incent_dict, get_submit_list
from db_builder import load_incent_text

MODEL = "gpt-5.4"

# DB 텍스트 최대 길이
# 한국어 1자 ≈ 1.5토큰 기준, 20000자 ≈ 30000토큰
MAX_DB_TEXT_CHARS = 20000

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# ─────────────────────────────────────────────
# 3-1. 업로드 파일 데이터 통합
# ─────────────────────────────────────────────

def build_user_context(
    biz_info: dict,
    hr_info: dict,
    vat_info: dict | None = None,
) -> str:
    lines = ["=== 사업주 정보 (업로드 파일 기반) ===\n"]

    lines.append("[사업자등록증]")
    for k, v in biz_info.items():
        if k != "parse_error" and v:
            lines.append(f"  {k}: {v}")

    if hr_info:
        lines.append("\n[인사정보]")
        lines.append(f"  전체 직원 수: {hr_info.get('total_employees', '알 수 없음')}명")
        lines.append(f"  현재 재직자 수: {hr_info.get('active_employees', '알 수 없음')}명")
        lines.append(f"  피보험자 수 (고용보험 가입): {hr_info.get('insured_count', '알 수 없음')}명")
        emp_types = hr_info.get("employment_types", {})
        if emp_types:
            emp_str = " / ".join(f"{k}: {v}명" for k, v in emp_types.items())
            lines.append(f"  고용형태: {emp_str}")
        lines.append(f"  청년 직원(15~34세): {hr_info.get('youth_count', 0)}명")
        lines.append(f"  고령 직원(60세+): {hr_info.get('elder_count', 0)}명")
        lines.append(f"  취업애로청년 해당 직원: {hr_info.get('youth_vulnerable_count', 0)}명")
        lines.append(f"  신규채용 직원: {hr_info.get('new_hire_count', 0)}명")
        lines.append(f"  사업주 관계자 (지원 제외 대상): {hr_info.get('owner_related_count', 0)}명")
        lines.append(f"  주근로시간 28시간 미만 직원: {hr_info.get('ineligible_hours_count', 0)}명")
        lines.append(f"  급여 450만원 초과 직원: {hr_info.get('over_salary_count', 0)}명")

    if vat_info and not vat_info.get("parse_error"):
        lines.append("\n[부가가치세 과세표준증명]")
        best = vat_info.get("best_year_sales")
        best_year = vat_info.get("best_year")
        if best:
            lines.append(f"  적용 연 매출액: {int(best):,}원 ({best_year}년 기준)")
        annual = vat_info.get("annual_sales", [])
        for s in annual:
            lines.append(f"  {s.get('year')}년 매출: {int(s.get('amount', 0)):,}원")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# youth_hire_incent 전용 전처리
# ─────────────────────────────────────────────

# 수도권 키워드
METROPOLITAN_KEYWORDS = ["서울", "인천", "경기"]

# 수도권이라도 비수도권으로 처리하는 인구감소지역 예외
METRO_EXCEPTION_KEYWORDS = ["강화군", "옹진군", "가평군", "연천군"]


def prefilter_youth_hire_incent(biz_info: dict, hr_info: dict | None = None, vat_info: dict | None = None) -> dict:
    """
    청년 일자리도약 장려금 전용 전처리.

    1) 수도권/비수도권 유형 판별 → 청년 요건 요약 주입
    2) 연 매출액 요건 확인 → 피보험자 수 × 19,000,000 이상
    3) 신청 및 지급 요건 하드코딩 주입 (PDF 파싱 불안정 대응)
    """
    address = biz_info.get("address", "") or ""

    # 수도권/비수도권 판별
    is_exception = any(kw in address for kw in METRO_EXCEPTION_KEYWORDS)
    is_metro_base = any(kw in address for kw in METROPOLITAN_KEYWORDS)
    is_metropolitan = is_metro_base and not is_exception

    if is_metropolitan:
        region_type = "수도권"
        region_context = """
[청년 일자리도약 장려금 — 수도권 유형 적용]
사업장 소재지: 수도권 (서울/인천/경기)

■ 청년 지원 요건 (아래 1-1, 1-2, 1-3 중 하나, 1-4 모두 충족 필요)
  1-1. 채용일 현재 만 15세 이상 34세 이하 (군필자 최고 만 39세)
  1-2. 채용일 현재 취업 중이 아닌 자 (고용보험 미가입, 프리랜서 3개월 이하, 사업자 미등록)
  1-3. 취업애로청년 (다음 ❶~❿ 중 하나에 해당):
       ❶ 연속 4개월 이상 실업 상태
       ❷ 고졸 이하 학력
       ❸ 고용촉진장려금 지급 대상 (취업지원프로그램 이수 + 구직등록)
       ❹ 국민취업지원제도 참여 후 최초 취업
       ❺ 청년도전지원사업 수료
       ❻ 자립준비청년/보호연장청년/청소년복지시설 입퇴소 청년
       ❼ 대량고용변동 신고 사업장 이직 후 최초 취업
       ❽ 북한이탈청년
       ❾ 자영업 폐업 후 최초 취업
       ❿ 최종학교 졸업 후 고용보험 총 가입기간 12개월 미만
  1-4. 기간의 정함이 없는 근로계약 + 고용보험 가입 + 주 28시간 이상 + 최저임금 이상 + 월 450만원 이하

※ 취업애로청년 요건(1-3) 확인 방법: 고용24 또는 워크넷
"""
    else:
        region_type = "비수도권"
        region_context = """
[청년 일자리도약 장려금 — 비수도권 유형 적용]
사업장 소재지: 비수도권 (서울/인천/경기 외 지역)

■ 청년 지원 요건 (아래 1-1, 1-2, 1-4 모두 충족 필요)
  1-1. 채용일 현재 만 15세 이상 34세 이하 (군필자 최고 만 39세)
  1-2. 채용일 현재 취업 중이 아닌 자 (고용보험 미가입, 프리랜서 3개월 이하, 사업자 미등록)
  1-4. 기간의 정함이 없는 근로계약 + 고용보험 가입 + 주 28시간 이상 + 최저임금 이상 + 월 450만원 이하

※ 비수도권 유형은 취업애로청년(1-3) 요건이 완전히 제외됨.
   취업애로청년 여부를 확인하거나 요구할 필요 없음.

■ 추가 혜택 (인구감소지역 해당 시)
  - 우대지원지역(44개): 청년장기근속인센티브 최대 600만원 (6·12·18·24개월 각 150만원)
  - 특별지원지역(40개): 청년장기근속인센티브 최대 720만원 (6·12·18·24개월 각 180만원)
"""

    # ── 연 매출액 요건 확인 ──────────────────
    sales_note = ""
    if hr_info and vat_info and not vat_info.get("parse_error"):
        insured = hr_info.get("insured_count", 0)
        best_sales = vat_info.get("best_year_sales", 0) or 0
        threshold = insured * 19_000_000
        if insured > 0 and threshold > 0:
            if best_sales >= threshold:
                sales_note = f"""
[매출액 요건 전처리 결과]
  피보험자 수: {insured}명
  기준 매출액: {threshold:,}원 (피보험자 수 × 19,000,000)
  실제 연 매출액: {int(best_sales):,}원
  → 매출액 요건 충족 ✅
"""
            else:
                sales_note = f"""
[매출액 요건 전처리 결과]
  피보험자 수: {insured}명
  기준 매출액: {threshold:,}원 (피보험자 수 × 19,000,000)
  실제 연 매출액: {int(best_sales):,}원
  → 매출액 요건 미충족 ❌ (기준 대비 {threshold - int(best_sales):,}원 부족)
  → 이 항목은 ineligible 처리하지 말고 need_check로 분류할 것.
     (과세표준증명이 실제 매출과 다를 수 있으므로 사업주 확인 필요)
"""
    elif not vat_info:
        sales_note = """
[매출액 요건 전처리 결과]
  부가가치세 과세표준증명 미업로드 — 매출액 요건은 need_check로 분류할 것.
"""

    # ── 신청 및 지급 요건 하드코딩 ──────────
    application_requirements = """
[신청 및 지급 요건 — 하드코딩 (DB 파싱 보완)]

■ 사업주 신청 요건
  A. 고용보험 적용 사업주
  B. 신청일 기준 고용보험 체납 없을 것
  C. 임금체불 사업주 명단 공개 중이 아닐 것
  D. 지원금 부정수급 제재 기간 중이 아닐 것
  E. 국가·지자체·공공기관·사회적기업 등 제외 업종 아닐 것
  F. 도박·향락·퇴폐업종 등 지원 제외 업종 아닐 것

■ 지급 요건 (신청 후 지급 단계 확인 사항)
  1. 지원 대상 청년을 지원 신청일 이후 채용 + 6개월간 고용 유지
  2. 지원금 신청은 신규 채용 후 3개월 이상~6개월 이내 신청
  3. 지원 기간 중 기준 피보험자 수 유지 (이탈 시 지급 중단)
  4. 지원 기간 중 임금체불·고용보험 체납 없을 것
  5. 지원 청년의 월 급여가 최저임금 이상 ~ 450만원 이하 유지

■ 지원 금액
  - 기업지원금: 월 최대 60만원 × 최대 12개월 = 최대 720만원/인
  - 비수도권 장기근속인센티브 (청년에게 별도 지급):
    · 일반 비수도권: 6·12·18·24개월 각 120만원 → 최대 480만원
    · 우대지원지역: 6·12·18·24개월 각 150만원 → 최대 600만원
    · 특별지원지역: 6·12·18·24개월 각 180만원 → 최대 720만원
"""

    return {
        "region_type":    region_type,
        "region_context": (region_context + sales_note + application_requirements).strip(),
    }


# ─────────────────────────────────────────────
# GPT 분석 시스템 프롬프트
# ─────────────────────────────────────────────

ANALYSIS_SYSTEM_PROMPT = """
당신은 대한민국 고용 지원금 전문 컨설턴트입니다.
사업주의 정보와 지원금 자격 요건을 비교하여 아래 JSON 형식으로만 응답하세요.
JSON 외 다른 텍스트는 절대 포함하지 마세요. 마크다운 코드블록도 제거하세요.

[중요 판단 원칙]
1. 프롬프트에 [전처리 결과]가 포함된 경우, 해당 내용을 DB보다 우선하여 판단하세요.
   전처리 결과에 명시된 유형(수도권/비수도권)의 요건만 적용하고,
   다른 유형의 요건은 분석에서 완전히 제외하세요.
2. 업로드 파일에서 확인 가능한 정보(소재지, 업종, 직원 수 등)를 최대한 활용하세요.
3. 확인이 불가능한 요건은 ineligible이 아닌 need_check 또는 need_doc으로 분류하세요.
4. ineligible은 어떤 유형에도 해당하지 않아 신청 자체가 불가능한 경우에만 사용하세요.

응답 JSON 형식:
{
  "incent_key": "<지원금 키>",
  "incent_name": "<지원금 이름>",
  "status": "eligible" | "conditional" | "ineligible",
  "status_reason": "<판정 근거 1~2문장>",
  "max_amount": "<지원 최대 금액 요약>",
  "official_url": "<공식 안내 URL 또는 빈 문자열>",

  "employer_requirements": {
    "ineligible": [
      {
        "item": "<부적격 요건 — 어떤 유형에도 해당하지 않는 경우에만>",
        "reason": "<부적격 판단 근거>"
      }
    ],
    "eligible": [
      {
        "item": "<업로드 파일로 충족이 확인된 요건>",
        "basis": "<판단 근거 (어떤 파일/데이터 기준인지)>"
      }
    ],
    "need_doc": [
      {
        "item": "<서류 제출로 확인해야 하는 요건>",
        "doc_name": "<필요한 서류명>",
        "how_to_get": "<발급처 또는 방법>",
        "satisfied": null
      }
    ],
    "need_check": [
      {
        "item": "<인트라넷/시스템 조회로 확인해야 하는 요건>",
        "how_to_check": "<확인 방법 — 고용24 / 워크넷 / 인사 기록 중 하나>",
        "satisfied": null
      }
    ],
    "or_groups": [
      {
        "description": "<'다음 중 하나' 형태의 OR 조건 설명>",
        "items": [
          {
            "item": "<OR 조건 항목>",
            "how_to_check": "<확인 방법>",
            "satisfied": null
          }
        ]
      }
    ]
  },

  "worker_requirements": {
    "label": "<근로자 유형 명칭 — ex) 청년, 고령자, 취업취약계층>",
    "ineligible": [],
    "eligible": [],
    "need_doc": [],
    "need_check": [],
    "or_groups": []
  }
}

분류 기준:
- ineligible  : 어떤 유형에도 해당하지 않아 신청 자체가 불가능한 경우에만 사용
- eligible    : 업로드 파일만으로 충족이 확인된 요건
- need_doc    : 별도 서류를 제출해야 확인 가능한 요건
- need_check  : 고용24 / 워크넷 / 회사 내 인사 기록 등 시스템 조회로 확인해야 하는 요건
- or_groups   : '다음 중 하나에 해당' 형태의 OR 조건 묶음

how_to_check 값은 반드시 다음 중 하나만 사용:
  "고용24" | "워크넷" | "회사 내 인사 기록"

근로자 요건이 없는 지원금은 worker_requirements의 모든 배열을 []로 두세요.
"""


# ─────────────────────────────────────────────
# 지원금별 전처리 함수 매핑
# ─────────────────────────────────────────────

PREFILTER_MAP = {
    "youth_hire_incent": prefilter_youth_hire_incent,
    # 추후 다른 지원금 전처리 함수 추가 가능
}


# ─────────────────────────────────────────────
# 3-2 / 4-1. GPT 분석 (단일 지원금)
# ─────────────────────────────────────────────

def analyze_single_incent(
    incent_key: str,
    user_context: str,
    incent_db_text: str,
    biz_info: dict,
    hr_info: dict | None = None,
    vat_info: dict | None = None,
) -> dict:
    # DB 텍스트 길이 제한
    if len(incent_db_text) > MAX_DB_TEXT_CHARS:
        print(f"[analyzer] '{incent_key}' DB 텍스트 {len(incent_db_text)}자 → {MAX_DB_TEXT_CHARS}자로 잘라냄")
        incent_db_text = incent_db_text[:MAX_DB_TEXT_CHARS]

    # 지원금별 전처리 실행
    prefilter_note = ""
    prefilter_fn = PREFILTER_MAP.get(incent_key)
    if prefilter_fn:
        prefilter_result = prefilter_fn(biz_info, hr_info, vat_info)
        region_type = prefilter_result.get("region_type", "")
        region_context = prefilter_result.get("region_context", "")
        prefilter_note = f"\n\n[전처리 결과 — DB보다 우선 적용]\n{region_context}"
        print(f"[analyzer] '{incent_key}' 전처리 완료 → {region_type} 유형 적용")

    submit_docs = get_submit_list(incent_key)
    submit_note = ""
    if submit_docs:
        submit_note = "\n\n[이 지원금의 기본 제출 서류 목록 (반드시 need_doc에 포함)]\n"
        submit_note += "\n".join(f"- {d}" for d in submit_docs)

    user_message = f"""
{user_context}

=== 지원금 자격 요건 DB ===
지원금 키: {incent_key}
{incent_db_text}{prefilter_note}{submit_note}

위 사업주가 이 지원금을 신청할 수 있는지 분석하고 JSON으로 반환하세요.
"""

    response = client.chat.completions.create(
        model=MODEL,
        max_completion_tokens=3000,
        messages=[
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
    )

    raw = response.choices[0].message.content.strip()
    print(f"[analyzer] '{incent_key}' finish_reason: {response.choices[0].finish_reason}, 응답 길이: {len(raw)}자")
    display_name = next((k for k, v in incent_dict.items() if v == incent_key), incent_key)

    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)
        result["incent_key"]  = incent_key
        result["incent_name"] = display_name
        return result
    except json.JSONDecodeError:
        print(f"[DEBUG] GPT raw 응답:\n{raw}")
        return {
            "incent_key":      incent_key,
            "incent_name":     display_name,
            "status":          "conditional",
            "status_reason":   "GPT 응답 파싱 오류 — 수동 확인 필요",
            "max_amount":      "",
            "official_url":    "",
            "employer_requirements": {
                "ineligible": [], "eligible": [],
                "need_doc": [], "need_check": [], "or_groups": []
            },
            "worker_requirements": {
                "label": "", "ineligible": [], "eligible": [],
                "need_doc": [], "need_check": [], "or_groups": []
            },
            "_raw_response": raw,
        }


# ─────────────────────────────────────────────
# 4-2. 전체 지원금 일괄 분석
# ─────────────────────────────────────────────

def analyze_all_incentives(
    biz_info: dict,
    hr_info: dict,
    vat_info: dict | None = None,
) -> list[dict]:
    user_context = build_user_context(biz_info, hr_info, vat_info)

    results = []
    for display_name, incent_key in incent_dict.items():
        print(f"[analyzer] 분석 중: {display_name} ({incent_key})")
        db_text = load_incent_text(incent_key)
        if not db_text:
            print(f"[analyzer] '{incent_key}' DB 없음 → 스킵")
            continue
        result = analyze_single_incent(incent_key, user_context, db_text, biz_info, hr_info, vat_info)
        results.append(result)

    order = {"eligible": 0, "conditional": 1, "ineligible": 2}
    results.sort(key=lambda r: order.get(r.get("status", "ineligible"), 2))
    return results
