"""
app.py
채용 지원금 추천 시스템 — Streamlit 메인 앱

실행:
    streamlit run app.py
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from db_builder import ensure_db
from file_parser import parse_biz_registration, parse_hr_info, parse_vat_certificate
from analyzer import analyze_all_incentives

from pages.upload_page import page_upload
from pages.confirm_page import page_confirm
from pages.results_page import page_results
from pages.form_page import page_form
from pages.parental_page import page_parental

# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="지원금뚝딱",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# 글로벌 스타일 (목업 디자인 시스템)
# ─────────────────────────────────────────────
st.markdown("""
<style>
  /* 전체 배경 */
  [data-testid="stAppViewContainer"] > .main { background: #F0F4F8; }
  [data-testid="stAppViewContainer"] { background: #F0F4F8; }
  /* 기본 헤더/푸터 제거 */
  header[data-testid="stHeader"] { display: none; }
  #MainMenu { display: none; }
  footer { display: none; }
  /* 메인 패딩 */
  .block-container { padding: 24px 28px 40px !important; max-width: 1060px !important; }
  /* 사이드바 스타일 */
  [data-testid="stSidebar"] {
    background: #263238 !important;
  }
  [data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    border: none !important;
    color: rgba(255,255,255,0.6) !important;
    text-align: left !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    border-radius: 0 !important;
    padding: 10px 18px !important;
    width: 100% !important;
    border-left: 3px solid transparent !important;
  }
  [data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: rgba(43,196,154,0.18) !important;
    color: #2BC49A !important;
    font-weight: 700 !important;
    border-left: 3px solid #2BC49A !important;
  }

  /* 카드 */
  .dd-card {
    background: #FFFFFF;
    border-radius: 12px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
    padding: 20px;
    margin-bottom: 14px;
  }
  /* 배지 */
  .dd-badge { display:inline-block; border-radius:20px; padding:2px 9px; font-size:11px; font-weight:700; white-space:nowrap; }
  .dd-badge-mint   { background:#E6F9F3; color:#1A9C7A; }
  .dd-badge-orange { background:#FFF3E0; color:#F57C00; }
  .dd-badge-red    { background:#FEECEB; color:#E53935; }
  .dd-badge-blue   { background:#EAF1FB; color:#3A7BD5; }
  .dd-badge-gray   { background:#F0F3F6; color:#546E7A; }

  /* 알림 배너 */
  .dd-alert-info    { background:#EAF1FB; border-left:4px solid #3A7BD5; border-radius:8px; padding:10px 14px; font-size:13px; color:#263238; margin-bottom:12px; }
  .dd-alert-warn    { background:#FFF3E0; border-left:4px solid #F57C00; border-radius:8px; padding:10px 14px; font-size:13px; color:#263238; margin-bottom:12px; }
  .dd-alert-success { background:#E6F9F3; border-left:4px solid #2BC49A; border-radius:8px; padding:10px 14px; font-size:13px; color:#263238; margin-bottom:12px; }
  .dd-alert-error   { background:#FEECEB; border-left:4px solid #E53935; border-radius:8px; padding:10px 14px; font-size:13px; color:#263238; margin-bottom:12px; }

  /* 구분선 */
  .dd-divider { border:none; border-top:1px solid #E0E8EE; margin:16px 0; }

  /* 버튼 */
  .stButton > button { border-radius:8px !important; font-weight:600 !important; font-size:13px !important; }
  .stButton > button[kind="primary"] { background:#2BC49A !important; border:none !important; color:#fff !important; }
  .stButton > button[kind="primary"]:hover { background:#1A9C7A !important; }

  /* 취업애로청년 요건 리스트 */
  .vuln-req-list { background:#F8FAFB; border:1px solid #E0E8EE; border-radius:8px; padding:14px 18px; margin:8px 0 12px; }
  .vuln-req-list li { font-size:13px; color:#263238; line-height:1.9; margin-left:6px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 세션 상태 초기화 (페이지별 독립 보존)
# ─────────────────────────────────────────────
_defaults = {
    "page":           "upload",   # upload | confirm | results
    "biz_info":       None,
    "hr_info":        None,
    "vat_info":       None,
    "results":        None,       # 기업관리 이동 시 초기화 안 됨
    "vuln_confirmed": False,
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─────────────────────────────────────────────
# 앱 시작 시 DB 확인
# ─────────────────────────────────────────────
with st.spinner("지원금 DB 확인 중..."):
    if "db_initialized" not in st.session_state:

        ensure_db()

    st.session_state[
        "db_initialized"
    ] = True


# ─────────────────────────────────────────────
# 사이드바 네비게이션 (목업 스타일)
# ─────────────────────────────────────────────
st.sidebar.markdown("""
<div style="padding:4px 0 22px; display:flex; align-items:center; gap:8px;">
  <div style="width:32px;height:32px;background:#2BC49A;border-radius:8px;
              display:flex;align-items:center;justify-content:center;font-size:16px;">⚡</div>
  <span style="font-weight:800;font-size:15px;color:#fff;">지원금뚝딱</span>
</div>
""", unsafe_allow_html=True)

_nav_items = [
    ("upload",  "📁", "파일 업로드"),
    ("confirm", "🔍", "정보 확인"),
    ("results", "🎯", "지원금 추천"),
    ("form", "📝", "신청서 작성"),
    ("parental", "👶", "육아휴직")
]
for _pid, _icon, _lbl in _nav_items:
    _active = st.session_state.page == _pid
    if st.sidebar.button(
        f"{_icon}  {_lbl}",
        key=f"nav_{_pid}",
        use_container_width=True,
        type="primary" if _active else "secondary",
    ):
        # results는 초기화 없이 페이지만 전환 (세션 보존)
        st.session_state.page = _pid
        st.rerun()

st.sidebar.markdown("<hr style='border-top:1px solid rgba(255,255,255,0.08);margin:16px 0;'>", unsafe_allow_html=True)
st.sidebar.markdown("""
<div style="font-size:11px;color:rgba(255,255,255,0.4);">노무법인 한빛</div>
<div style="font-size:13px;font-weight:600;color:rgba(255,255,255,0.8);">관리자</div>
""", unsafe_allow_html=True)




# ─────────────────────────────────────────────
# 라우팅
# ─────────────────────────────────────────────
_page = st.session_state.page

if _page == "upload":
    page_upload()
elif _page == "confirm":
    if st.session_state.biz_info is None:
        st.markdown('<div class="dd-alert-warn">⚠️ 파일을 먼저 업로드해주세요.</div>', unsafe_allow_html=True)
        st.session_state.page = "upload"
        st.rerun()
    else:
        page_confirm()
elif _page == "results":
    if st.session_state.biz_info is None:
        st.markdown('<div class="dd-alert-warn">⚠️ 파일을 먼저 업로드해주세요.</div>', unsafe_allow_html=True)
        st.session_state.page = "upload"
        st.rerun()
    else:
        page_results()
elif _page == "form":
    if st.session_state.results is None:
        st.session_state.page = "upload"
        st.rerun()
    else:
        page_form()
elif _page == "parental":
    page_parental()
    









