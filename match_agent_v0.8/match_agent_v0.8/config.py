"""
config.py
지원금 DB 설정 (1-1 ~ 1-5)
"""

import os

# ─────────────────────────────────────────────
# 1-1. 지원금 리스트
# ─────────────────────────────────────────────
incent_dict = {

    # ─────────────────────────────
    # 기존 고용 지원
    # ─────────────────────────────
    "청년 일자리도약 장려금":
        "youth_hire_incent",

    "고용촉진장려금":
        "employ_promo_incent",

    "정규직 전환 지원":
        "perm_conv_incent",

    "고령자 고용지원금":
        "elders_employ_incent",


    # ─────────────────────────────
    # 육아 돌봄
    # ─────────────────────────────
    "육아휴직 육아기 근로시간 단축지원금":
        "parental_leave_reduction_support",

    "대체인력 업무분담지원금":
        "replacement_workshare_support",


    # ─────────────────────────────
    # 10시 출근 & 노동시간 단축
    # ─────────────────────────────
    "워라밸+4.5 프로젝트":
        "worklife_balance_45_support",

    "육아기 10시 출근 지원":
        "childcare_flexible_start_support",

    "소정근로 단축 지원":
        "working_hours_reduction_support",


    # ─────────────────────────────
    # 유연근무
    # ─────────────────────────────
    "유연근무 장려금":
        "flexible_work_incent",

    "유연근무제 시스템 구축 지원":
        "flexible_work_system_support"
}

# ─────────────────────────────────────────────
# 1-2. 지원금별 URL
#    'none' → URL 크롤링 없음, incent_docs 폴더에 수동으로 파일 넣어야 함
# ─────────────────────────────────────────────
incent_urls = {
    "youth_hire_incent":    "none",
    
    "employ_promo_incent":  "https://m.work24.go.kr/cm/c/f/1100/selecSystInfo.do?currentPageNo=1&recordCountPerPage=9&upprSystClId=&systClId=SC00000119&systId=SI00000370",
    "perm_conv_incent":     "https://m.work24.go.kr/cm/c/f/1100/selecSystInfo.do?currentPageNo=1&recordCountPerPage=9&upprSystClId=&systClId=SC00000390&systId=SI00000505",
    "elders_employ_incent": "https://m.work24.go.kr/cm/c/f/1100/selecSystInfo.do?currentPageNo=1&recordCountPerPage=9&upprSystClId=&systClId=SC00000121&systId=SI00000328",
   
   
    "parental_leave_reduction_support": "https://www.worklife.kr/website_renew/index/employerSupport/parental_leave_reduction_subsidy.asp",
        
    "replacement_workshare_support": "https://www.worklife.kr/website_renew/index/employerSupport/substitute_worker_subsidy.asp",
    

    "worklife_balance_45_support": "https://www.worklife.kr/website_renew/index/employerSupport/week_4_5_day_support.asp",
    
    "childcare_flexible_start_support": "https://www.worklife.kr/website_renew/index/employerSupport/flexible_work_10am_support.asp",
    
    
    "working_hours_reduction_support": "https://www.worklife.kr/website_renew/index/employerSupport/reduced_work_hours_subsidy.asp",

   
   "flexible_work_incent": "https://www.worklife.kr/website_renew/index/employerSupport/flexible_work_bonus.asp",
   "flexible_work_system_support": "https://www.worklife.kr/website_renew/index/employerSupport/work_life_balance_system_support.asp"
}

# ─────────────────────────────────────────────
# 1-3. incent_docs 폴더 경로
#   각 지원금 자격 요건 서류(PDF/TXT)가 저장된 폴더
#   ex) incent_docs/youth_hire_incent_docs/
# ─────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
INCENT_DOCS_ROOT = os.path.join(BASE_DIR, "incent_docs")

incent_docs_dirs = {
    key: os.path.join(INCENT_DOCS_ROOT, f"{key}_docs")
    for key in incent_dict.values()
}

# ─────────────────────────────────────────────
# 1-4. 크롤링 저장 형식
#   저장 형식: JSON (구조화) + TXT (원문)
#   - {incent_key}_raw.txt    : 크롤링 원문
#   - {incent_key}_meta.json  : 제목, 수집일, URL 메타정보
# ─────────────────────────────────────────────
CRAWL_ENCODING = "utf-8"
CRAWL_TARGET_CSS = "div.cont_wrap_area"   # 크롤링 대상 CSS 선택자

# ─────────────────────────────────────────────
# 1-5. 지원금별 추가 제출 서류
# ─────────────────────────────────────────────
submit_dict = {
    "youth_hire_incent":    "youth_hire_incent_submit",
    "employ_promo_incent":  "employ_promo_incent_submit",
    "perm_conv_incent":     "perm_conv_incent_submit",
    "elders_employ_incent": "elders_employ_incent_submit",
}

youth_hire_incent_submit = [
    "연소자 증명서",
    "친권자 동의",
    "가족관계증명서",
    "최종 학력에 대한 자기 확인서",
]

employ_promo_incent_submit = [
    "워크넷 입사 확인서",
    "근로계약서 사본",
]

perm_conv_incent_submit = [
    "전환 전 근로계약서 사본",
    "전환 후 근로계약서 사본",
    "취업규칙(변경) 사본",
]

elders_employ_incent_submit = [
    "분기 고령자 고용 현황 확인서",
]

# submit_dict value → 실제 리스트 매핑
submit_lists = {
    "youth_hire_incent_submit":    youth_hire_incent_submit,
    "employ_promo_incent_submit":  employ_promo_incent_submit,
    "perm_conv_incent_submit":     perm_conv_incent_submit,
    "elders_employ_incent_submit": elders_employ_incent_submit,
}

def get_submit_list(incent_key: str) -> list[str]:
    """incent_key → 제출 서류 리스트 반환"""
    list_name = submit_dict.get(incent_key, "")
    return submit_lists.get(list_name, [])
