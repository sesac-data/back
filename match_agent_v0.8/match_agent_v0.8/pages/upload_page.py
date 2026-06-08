# ─────────────────────────────────────────────
# STEP 1: 파일 업로드
# ─────────────────────────────────────────────
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(CURRENT_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from file_parser import (
    parse_biz_registration,
    parse_hr_info,
    parse_vat_certificate
)

from utils.ui_helpers import step_indicator

import streamlit as st


def page_upload() -> None:
    step_indicator()
    st.markdown("""
    <div style="margin-bottom:20px;">
      <h2 style="font-size:22px;font-weight:800;color:#263238;margin:0;">사업주 서류 업로드</h2>
      <p style="color:#94A8B6;font-size:13px;margin:4px 0 0;">
        아래 서류를 업로드하면 신청 가능한 채용 지원금을 자동으로 분석합니다.
      </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="dd-card" style="padding:16px 18px 12px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-weight:700;font-size:14px;color:#263238;margin-bottom:8px;">🏢 사업자등록증 <span class="dd-badge dd-badge-red">필수</span></div>', unsafe_allow_html=True)
        biz_file = st.file_uploader("사업자등록증", type=["pdf","jpg","jpeg","png","gif"], key="biz_uploader", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="dd-card" style="padding:16px 18px 12px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-weight:700;font-size:14px;color:#263238;margin-bottom:8px;">👥 인사정보(제출) <span class="dd-badge dd-badge-red">필수</span></div>', unsafe_allow_html=True)
        hr_file = st.file_uploader("인사정보", type=["xlsx","xls"], key="hr_uploader", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="dd-card" style="padding:16px 18px 12px;">', unsafe_allow_html=True)
    st.markdown('<div style="font-weight:700;font-size:14px;color:#263238;margin-bottom:2px;">💰 부가가치세 과세표준증명 <span class="dd-badge dd-badge-blue">권장</span></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:12px;color:#94A8B6;margin-bottom:8px;">매출액 기준 충족 여부 자동 계산에 사용됩니다.</div>', unsafe_allow_html=True)
    vat_file = st.file_uploader("부가가치세", type=["pdf"], key="vat_uploader", label_visibility="collapsed")
    st.markdown('</div>', unsafe_allow_html=True)

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        if st.button("분석 시작 →", type="primary", use_container_width=True):
            if biz_file is None or hr_file is None:
                st.markdown('<div class="dd-alert-error">⚠️ 사업자등록증과 인사정보 파일은 필수입니다.</div>', unsafe_allow_html=True)
                return
            with st.spinner("파일 파싱 중..."):
                st.session_state.biz_info = parse_biz_registration(biz_file.read(), biz_file.name)
                st.session_state.hr_info  = parse_hr_info(hr_file.read())
                st.session_state.vat_info = parse_vat_certificate(vat_file.read()) if vat_file else {}
                # 새 파일 업로드 시 이전 분석 결과 초기화
                st.session_state.results        = None
                st.session_state.vuln_confirmed = False
            st.session_state.page = "confirm"
            st.rerun()
