# ─────────────────────────────────────────────
# STEP 3: 지원금 추천 결과
# ─────────────────────────────────────────────

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(CURRENT_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from analyzer import analyze_all_incentives
from utils.ui_helpers import step_indicator, _render_requirements, _has_conditional, STATUS_LABEL
import streamlit as st


def page_results() -> None:
    step_indicator()

    # 분석 실행 (results가 None일 때만 — 페이지 이동 후 돌아와도 재실행 안 함)
    if st.session_state.results is None:
        with st.spinner("GPT가 지원금 자격을 분석 중입니다..."):
            results = analyze_all_incentives(
                st.session_state.biz_info or {},
                st.session_state.hr_info  or {},
                st.session_state.vat_info or {},
            )
            st.session_state.results = results
        st.rerun()
        return

    results: list[dict] = st.session_state.results

    st.markdown("""
    <div style="margin-bottom:18px;">
      <h2 style="font-size:22px;font-weight:800;color:#263238;margin:0;">지원금 분석 결과</h2>
    </div>
    """, unsafe_allow_html=True)

    # KPI 카드
    eligible    = sum(1 for r in results if r.get("status") == "eligible")
    conditional = sum(1 for r in results if r.get("status") == "conditional")
    ineligible  = sum(1 for r in results if r.get("status") == "ineligible")

    kpi_cols = st.columns(4)
    for col, (lbl, val, color) in zip(kpi_cols, [
        ("검토한 지원금", str(len(results)), "#3A7BD5"),
        ("✅ 신청 가능",  str(eligible),    "#2BC49A"),
        ("⚠️ 조건부",    str(conditional), "#F57C00"),
        ("❌ 미충족",     str(ineligible),  "#E53935"),
    ]):
        col.markdown(f"""
        <div class="dd-card" style="padding:16px 18px;text-align:center;">
          <div style="font-size:11px;color:#94A8B6;margin-bottom:4px;">{lbl}</div>
          <div style="font-size:28px;font-weight:800;color:{color};">{val}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="dd-alert-info">⚠️ 아래 결과는 AI 분석 기반 참고 정보입니다. 실제 신청 전 <strong>고용24</strong> 또는 <strong>담당 기관</strong>에서 최종 자격을 확인하세요.</div>', unsafe_allow_html=True)

    # 지원금별 expander
    for r_idx, r in enumerate(results):
        emp_reqs    = r.get("employer_requirements", {})
        worker_reqs = r.get("worker_requirements",  {})
        incent_key  = r.get("incent_key", "")

        if bool(emp_reqs.get("ineligible")) or bool(worker_reqs.get("ineligible")):
            display_status = "ineligible"
        elif _has_conditional(emp_reqs) or _has_conditional(worker_reqs):
            display_status = "conditional"
        else:
            display_status = "eligible"

        icon, label, color = STATUS_LABEL.get(display_status, ("🔲", "확인 필요", "#94A8B6"))

        with st.expander(
            f"{icon} {r.get('incent_name', incent_key)}  —  {r.get('max_amount', '')}",
            expanded=(display_status in ("eligible", "conditional")),
        ):
            st.markdown(
                f'<span class="dd-badge" style="background:{color}22;color:{color};">{icon} {label}</span>'
                f'&nbsp;&nbsp;<span style="font-size:13px;color:#546E7A;">{r.get("status_reason","")}</span>',
                unsafe_allow_html=True,
            )

            st.markdown("<hr class='dd-divider'>", unsafe_allow_html=True)
            st.markdown("### 🏢 기업 자격 요건")
            skip_worker = _render_requirements(emp_reqs, f"emp_{r_idx}", incent_key)

            if not skip_worker:
                worker_label = worker_reqs.get("label", "근로자")
                has_worker = any([
                    worker_reqs.get("ineligible"), worker_reqs.get("eligible"),
                    worker_reqs.get("need_doc"),   worker_reqs.get("need_check"),
                    worker_reqs.get("or_groups"),
                ])
                if has_worker:
                    st.markdown("<hr class='dd-divider'>", unsafe_allow_html=True)
                    st.markdown(f"### 👤 {worker_label} 자격 요건")
                    _render_requirements(worker_reqs, f"worker_{r_idx}", incent_key)

            if r.get("official_url"):
                st.markdown(f"[🔗 공식 안내 보기 →]({r['official_url']})")

    st.markdown("<hr class='dd-divider'>", unsafe_allow_html=True)
    col_back, col_doc, _ = st.columns([1, 2, 3])
    with col_back:
        if st.button("← 처음으로"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()
    with col_doc:
        if st.button("📝 신청서 작성하기"):
            st.session_state.page = 'form'
            st.rerun()
