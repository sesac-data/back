# ─────────────────────────────────────────────
# STEP 2: 파싱 결과 확인
# ─────────────────────────────────────────────

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(CURRENT_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import streamlit as st
from utils.ui_helpers import step_indicator


def page_confirm() -> None:
    step_indicator()
    st.markdown('<p style="color:#94A8B6;font-size:13px;margin:-8px 0 16px;">추출된 정보를 확인하세요. 오류가 있으면 이전 단계에서 파일을 교체하세요.</p>', unsafe_allow_html=True)

    biz = st.session_state.biz_info or {}
    hr  = st.session_state.hr_info  or {}
    vat = st.session_state.vat_info or {}

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('''<div class="dd-card">
          <div style="font-weight:700;font-size:16px;color:#263238;margin-bottom:12px;">🏢 기업 정보</div>''', unsafe_allow_html=True)
        if "parse_error" in biz:
            st.markdown(f'<div class="dd-alert-warn">OCR 오류: {biz["parse_error"]}</div>', unsafe_allow_html=True)
        else:
            for lbl, key in [
                ("상호", "company_name"), ("사업자등록번호", "business_reg_no"),
                ("대표자", "ceo_name"),
            ]:
                if biz.get(key):
                    st.markdown(f"<div style='font-size:14px;padding:3px 0;'><span style='color:#94A8B6;min-width:110px;display:inline-block;'>{lbl}</span> <strong>{biz[key]}</strong></div>", unsafe_allow_html=True)
            # 표준산업분류코드 업태 위에
            if hr.get("industry_code"):
                st.markdown(f"<div style='font-size:14px;padding:3px 0;'><span style='color:#94A8B6;min-width:110px;display:inline-block;'>표준산업분류코드</span> <strong>{hr['industry_code']}</strong></div>", unsafe_allow_html=True)
            for lbl, key in [
                ("업태", "business_type"), ("종목", "business_item"),
                ("개업 연월일", "open_date"), ("소재지", "address"),
            ]:
                if biz.get(key):
                    st.markdown(f"<div style='font-size:14px;padding:3px 0;'><span style='color:#94A8B6;min-width:110px;display:inline-block;'>{lbl}</span> <strong>{biz[key]}</strong></div>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('''<div class="dd-card">
          <div style="font-weight:700;font-size:16px;color:#263238;margin-bottom:12px;">👥 인사 정보</div>''', unsafe_allow_html=True)
        summary = [
            ("전체 직원",       f"{hr.get('total_employees', '-')}명"),
            ("현재 재직자",     f"{hr.get('active_employees', '-')}명"),
            ("피보험자 수",     f"{hr.get('insured_count', '-')}명"),
            ("청년(15~34세)",   f"{hr.get('youth_count', 0)}명"),
            ("고령자(60세+)",   f"{hr.get('elder_count', 0)}명"),
            ("취업애로청년",    f"{hr.get('youth_vulnerable_count', 0)}명"),
            ("신규채용",        f"{hr.get('new_hire_count', 0)}명"),
            ("사업주 관계자",   f"{hr.get('owner_related_count', 0)}명"),
        ]
        for lbl, val in summary:
            st.markdown(f"<div style='font-size:14px;padding:3px 0;'><span style='color:#94A8B6;min-width:110px;display:inline-block;'>{lbl}</span> <strong>{val}</strong></div>", unsafe_allow_html=True)
        if hr.get("ineligible_hours_count", 0) > 0:
            st.markdown(f'<div class="dd-alert-warn" style="margin-top:8px;">⚠️ 주 28시간 미만 직원 {hr["ineligible_hours_count"]}명 — 지원 제외</div>', unsafe_allow_html=True)
        if hr.get("over_salary_count", 0) > 0:
            st.markdown(f'<div class="dd-alert-warn" style="margin-top:4px;">⚠️ 급여 450만원 초과 직원 {hr["over_salary_count"]}명 — 지원 제외</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # 부가가치세
    if vat and not vat.get("parse_error"):
        st.markdown('''<div class="dd-card">
          <div style="font-weight:700;font-size:16px;color:#263238;margin-bottom:12px;">💰 부가가치세 과세표준증명</div>''', unsafe_allow_html=True)
        sales = vat.get("annual_sales", [])
        if sales:
            import pandas as pd
            vat_df = pd.DataFrame([{
                "과세연도": f"{s.get('year')}년",
                "과세기간": f"{s.get('period_start')} ~ {s.get('period_end')}",
                "과세표준 합계": f"{int(s.get('amount', 0)):,}원",
            } for s in sales])
            st.dataframe(vat_df, use_container_width=True, hide_index=True)
        best = vat.get("best_year_sales")
        if best:
            st.markdown(f'<div class="dd-alert-success">✅ 적용 매출액: <strong>{int(best):,}원</strong> ({vat.get("best_year")}년 기준)</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    elif not vat:
        st.markdown('<div class="dd-alert-info">ℹ️ 부가가치세 과세표준증명 미업로드 — 매출액 기준은 수동 확인이 필요합니다.</div>', unsafe_allow_html=True)

    # 직원 목록
    st.markdown('''<div class="dd-card">
      <div style="font-weight:700;font-size:16px;color:#263238;margin-bottom:12px;">👥 직원 목록</div>''', unsafe_allow_html=True)
    records = hr.get("records", [])
    if records:
        import pandas as pd
        df_display = pd.DataFrame(records)
        if "주민등록번호" in df_display.columns:
            df_display["주민등록번호"] = df_display["주민등록번호"].apply(
                lambda x: str(x)[:6] + "-*******" if pd.notna(x) and str(x) != "nan" else x
            )
        def highlight_row(row):
            if str(row.get("취업애로청년", "")).strip().upper() == "Y":
                return ["background-color: #FFF3E0"] * len(row)
            return [""] * len(row)
        st.dataframe(df_display.style.apply(highlight_row, axis=1), use_container_width=True, hide_index=True)
        st.caption("🟠 주황 배경: 취업애로청년 해당 직원")
    else:
        st.info("직원 데이터가 없습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("")
    col_back, col_next, _ = st.columns([1, 1, 4])
    with col_back:
        if st.button("← 다시 업로드"):
            st.session_state.page = "upload"
            st.rerun()
    with col_next:
        if st.button("지원금 분석 →", type="primary"):
            st.session_state.page = "results"
            st.rerun()
