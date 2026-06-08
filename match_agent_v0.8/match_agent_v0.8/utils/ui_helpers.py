# ─────────────────────────────────────────────
# 스텝 인디케이터
# ─────────────────────────────────────────────

import streamlit as st

def step_indicator() -> None:
    _order = ["upload", "confirm", "results", "form"]
    _labels = ["1  파일 업로드", "2  정보 확인", "3  지원금 추천", "4 신청서 작성"]
    cur = _order.index(st.session_state.page)
    cols = st.columns(4)
    for i, (col, lbl) in enumerate(zip(cols, _labels)):
        if i < cur:
            col.markdown(f"<div style='text-align:center;color:#2BC49A;font-weight:600;font-size:13px;'>{lbl} ✔</div>", unsafe_allow_html=True)
        elif i == cur:
            col.markdown(f"<div style='text-align:center;color:#3A7BD5;font-weight:700;font-size:13px;border-bottom:2px solid #3A7BD5;padding-bottom:4px;'>{lbl}</div>", unsafe_allow_html=True)
        else:
            col.markdown(f"<div style='text-align:center;color:#94A8B6;font-size:13px;'>{lbl}</div>", unsafe_allow_html=True)
    st.markdown("<hr class='dd-divider'>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 공통 헬퍼
# ─────────────────────────────────────────────

STATUS_LABEL = {
    "eligible":    ("✅", "신청 가능",   "#2BC49A"),
    "conditional": ("⚠️", "조건부 가능", "#F57C00"),
    "ineligible":  ("❌", "미충족",      "#E53935"),
}

YOUTH_VULNERABLE_REQUIREMENTS = [
    "❶ 연속 4개월 이상 실업 상태",
    "❷ 고졸 이하 학력",
    "❸ 고용촉진장려금 지급 대상 (취업지원프로그램 이수 + 구직등록)",
    "❹ 국민취업지원제도 참여 후 최초 취업",
    "❺ 청년도전지원사업 수료",
    "❻ 자립준비청년/보호연장청년/청소년복지시설 입퇴소 청년",
    "❼ 대량고용변동 신고 사업장 이직 후 최초 취업",
    "❽ 북한이탈청년",
    "❾ 자영업 폐업 후 최초 취업",
    "❿ 최종학교 졸업 후 고용보험 총 가입기간 12개월 미만",
]


def _has_conditional(reqs: dict) -> bool:
    for item in reqs.get("need_doc", []):
        if not item.get("satisfied"):
            return True
    for item in reqs.get("need_check", []):
        if not item.get("satisfied"):
            return True
    for grp in reqs.get("or_groups", []):
        if not any(i.get("satisfied") for i in grp.get("items", [])):
            return True
    return False


def _render_requirements(reqs: dict, section_key: str, incent_key: str = "") -> bool:
    """
    요건 섹션 렌더링.
    ineligible 있으면 True 반환 (이후 섹션 스킵 신호).
    수도권 youth_hire_incent의 취업애로청년 OR 그룹은
    체크박스 없는 전체 리스트 + 최종 단일 확인 체크박스로 렌더링.
    """
    # 1. 부적격
    ineligible_items = reqs.get("ineligible", [])
    if ineligible_items:
        for item in ineligible_items:
            st.markdown(f"""
            <div class="dd-alert-error">
              ❌ <strong>{item.get('item', '')}</strong><br>
              <span style="font-size:12px;">{item.get('reason', '')}</span>
            </div>
            """, unsafe_allow_html=True)
        return True

    # 2. 충족된 요건
    for item in reqs.get("eligible", []):
        st.markdown(f"""
        <div class="dd-alert-success">
          ✅ {item.get('item', '')}<br>
          <span style="font-size:11px;color:#546E7A;">근거: {item.get('basis', '')}</span>
        </div>
        """, unsafe_allow_html=True)

    # 3. 서류 제출 필요
    need_doc = reqs.get("need_doc", [])
    if need_doc:
        st.markdown("**📄 서류 제출 필요**")
        for i, item in enumerate(need_doc):
            checked = st.checkbox(
                label=item.get("item", ""),
                value=bool(item.get("satisfied")),
                key=f"{section_key}_doc_{i}",
            )
            item["satisfied"] = checked
            if item.get("doc_name"):
                st.caption(f"　📋 서류: **{item['doc_name']}**  |  📍 발급처: {item.get('how_to_get', '')}")

    # 4. 조회 필요
    need_check = reqs.get("need_check", [])
    if need_check:
        st.markdown("**🔍 개별 조회 필요**")
        for i, item in enumerate(need_check):
            checked = st.checkbox(
                label=item.get("item", ""),
                value=bool(item.get("satisfied")),
                key=f"{section_key}_check_{i}",
            )
            item["satisfied"] = checked
            st.caption(f"　📍 확인 방법: {item.get('how_to_check', '')}")

    # 5. OR 그룹
    for g_i, grp in enumerate(reqs.get("or_groups", [])):
        desc = grp.get("description", "")
        items = grp.get("items", [])
        is_vuln_group = incent_key == "youth_hire_incent" and "취업애로청년" in desc

        if is_vuln_group:
            # 취업애로청년: 체크박스 없는 전체 리스트 + 최종 확인 단일 체크박스
            st.markdown("**🔀 취업애로청년 요건 (다음 중 하나 해당)**")
            req_html = "<ul class='vuln-req-list'>"
            for req in YOUTH_VULNERABLE_REQUIREMENTS:
                req_html += f"<li>{req}</li>"
            req_html += "</ul>"
            st.markdown(req_html, unsafe_allow_html=True)

            confirmed = st.checkbox(
                "모든 신청인이 취업애로청년 요건 중 하나 이상에 해당됨을 확인함.",
                value=bool(st.session_state.get("vuln_confirmed", False)),
                key=f"{section_key}_vuln_confirm",
            )
            st.session_state.vuln_confirmed = confirmed
            for item in items:
                item["satisfied"] = confirmed
        else:
            st.markdown(f"**🔀 다음 중 하나 해당** — *{desc}*")
            for i_i, item in enumerate(items):
                checked = st.checkbox(
                    label=item.get("item", ""),
                    value=bool(item.get("satisfied")),
                    key=f"{section_key}_or_{g_i}_{i_i}",
                )
                item["satisfied"] = checked
                st.caption(f"　📍 확인 방법: {item.get('how_to_check', '')}")

    return False