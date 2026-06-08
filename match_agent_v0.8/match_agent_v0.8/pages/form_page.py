# ─────────────────────────────────────────────
# STEP 4: 신청서 작성
# ─────────────────────────────────────────────

import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(CURRENT_DIR)
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

import streamlit as st
from utils.ui_helpers import step_indicator

def page_form() -> None:
    step_indicator()
    biz = st.session_state.biz_info or {}
    hr  = st.session_state.hr_info or {}
    vat = st.session_state.vat_info or {}

    company_name = biz.get("company_name", "")
    ceo_name     = biz.get("ceo_name", "")
    biz_no       = biz.get("business_reg_no", "")
    address      = biz.get("address", "")

    st.markdown("""
    <div style="margin-bottom:18px;">
      <h2 style="font-size:22px;font-weight:800;color:#263238;margin:0;">신청서 작성</h2>
      <p style="color:#94A8B6;font-size:13px;margin-top:4px;">
        필요한 신청서를 선택하여 작성하세요.
      </p>
    </div>
    """, unsafe_allow_html=True)

    import streamlit.components.v1 as components

    # ✅ 서식 선택 (sidebar 제거 → 내부 radio)
    selected_form = st.radio(
        "작성할 신청서를 선택하세요",
        ["[서식 1] 참여 신청서 (사업장용)", "[서식 7 & 7-1] 지급 신청서 및 확인서"],
        horizontal=True
    )

    # ------------------------------------------------------------------
    # 서식 1
    # ------------------------------------------------------------------
    if selected_form == "[서식 1] 참여 신청서 (사업장용)":
        st.subheader("📄 참여 신청서")
        
        form1_html = f"""
        <div style="background-color: #525659; padding: 30px; display: flex; justify-content: center;">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
                .pdf-page {{
                    width: 820px;
                    background-color: white;
                    padding: 50px 60px;
                    font-family: 'Malgun Gothic', 'Noto Sans KR', sans-serif;
                    color: black;
                    font-size: 11px;
                    line-height: 1.5;
                }}
                .header-table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; }}
                .header-table td {{ border: 1px solid #000; padding: 5px; text-align: center; font-size: 10px; }}
                .main-title {{ text-align: center; font-size: 20px; font-weight: bold; margin: 15px 0; text-decoration: underline; }}
                .section-title {{ font-size: 13px; font-weight: bold; margin: 15px 0 5px 0; background: #f2f2f2; padding: 4px 10px; border-left: 4px solid #333; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; border: 1.2px solid #000; table-layout: fixed; }}
                th, td {{ border: 1px solid #000; padding: 4px 2px; font-size: 10.5px; height: 32px; text-align: center; overflow: hidden; }}
                th {{ background-color: #f8f8f8; font-weight: bold; }}
                .input-box {{ width: 95%; border: none; outline: none; background: #f0f7ff; font-weight: bold; color: #0033ff; font-size: 11px; text-align: center; }}
                .text-left {{ text-align: left; padding-left: 10px; }}
                .check-item {{ display: inline-flex; align-items: center; margin-right: 10px; margin-bottom: 3px; white-space: nowrap; }}
                .caption {{ font-size: 9px; color: #555; line-height: 1.4; margin-top: 2px; text-align: left; }}
            </style>

            <div class="pdf-page">
                <div style="text-align: right; font-weight: bold;">■ [서식 1]</div>
                <table class="header-table">
                    <tr>
                        <td width="15%" style="background:#f2f2f2;">접수번호</td>
                        <td width="35%"><input type="text" class="input-box" value="○○기관 - 2026-0000"></td>
                        <td width="15%" style="background:#f2f2f2;">접수일자</td>
                        <td width="35%"><input type="text" class="input-box" value="2026. 03. 24."></td>
                    </tr>
                </table>

                <div class="main-title">『청년일자리도약장려금 사업』 참여 신청서</div>

                <div class="section-title">1. 사업장 현황</div>
                <table>
                    <tr>
                        <th width="15%">사업장명</th><td width="35%"><input type="text" class="input-box" value="{company_name}" style="text-align:left;"></td>
                        <th width="15%">대표자명</th><td width="35%"><input type="text" class="input-box" value="{ceo_name}" style="text-align:left;"></td>
                    </tr>
                    <tr>
                        <th>사업자등록번호</th><td><input type="text" class="input-box" value="{biz_no}" style="text-align:left;"></td>
                        <th>법인등록번호</th><td><input type="text" class="input-box" value="20-222-2222" style="text-align:left;"></td>
                    </tr>
                    <tr>
                        <th>업종</th><td><input type="text" class="input-box" value="-" style="text-align:left;"></td>
                        <th>고용보험<br>사업장관리번호</th><td><input type="text" class="input-box" value="987-65-43210" style="text-align:left;"></td>
                    </tr>
                    <tr>
                        <th>소재지</th><td colspan="3"><input type="text" class="input-box" value="{address}" style="text-align:left;"></td>
                    </tr>
                </table>

                <div class="section-title">2. 기업 구분(지원대상 기업 여부 확인)</div>
                <div class="caption" style="margin-bottom:5px;">참여신청 직전 월부터 이전 1년간 매 월말 고용보험 피보험자 수 평균: <input type="text" style="width:30px; border-bottom:1px solid #000; border:none; text-align:center; font-weight:bold; color:#0033ff;" value="15"> 명</div>
                
                <table>
                    <tr style="background:#f9f9f9; font-size:9px;">
                        <th width="12%">구분</th>
                        <td>1월</td><td>2월</td><td>3월</td><td>4월</td><td>5월</td><td>6월</td><td>7월</td><td>8월</td><td>9월</td><td>10월</td><td>11월</td><td>12월</td>
                    </tr>
                    <tr>
                        <td style="font-size:9px; line-height:1.2;">해당 월말<br>피보험자수</td>
                        <td><input type="text" class="input-box" value="10"></td><td><input type="text" class="input-box" value="11"></td>
                        <td><input type="text" class="input-box" value="12"></td><td><input type="text" class="input-box" value="13"></td>
                        <td><input type="text" class="input-box" value="14"></td><td><input type="text" class="input-box" value="15"></td>
                        <td><input type="text" class="input-box" value="16"></td><td><input type="text" class="input-box" value="17"></td>
                        <td><input type="text" class="input-box" value="18"></td><td><input type="text" class="input-box" value="19"></td>
                        <td><input type="text" class="input-box" value="20"></td><td><input type="text" class="input-box" value="21"></td>
                    </tr>
                </table>

                <table>
                    <tr>
                        <th width="15%">기업 구분</th>
                        <td>
                            <div class="check-item"><input type="checkbox" checked> 우선지원대상기업</div>
                            <div class="check-item"><input type="checkbox"> 지식서비스산업</div>
                            <div class="check-item"><input type="checkbox"> 문화콘텐츠산업</div>
                            <div class="check-item"><input type="checkbox"> 신·재생에너지산업</div><br>
                            <div class="check-item"><input type="checkbox"> 청년창업기업</div>
                            <div class="check-item"><input type="checkbox"> 미래유망기업</div>
                            <div class="check-item"><input type="checkbox"> 지역주력산업</div>
                            <div class="check-item"><input type="checkbox"> 고용위기지역 기업</div>
                        </td>
                    </tr>
                    <tr>
                        <th>연 매출액</th>
                        <td>
                            과세 대상 기간 <input type="text" style="width:60px; border-bottom:1px solid #ccc; border:none; text-align:center;" value="2024.01"> 부터 
                            <input type="text" style="width:60px; border-bottom:1px solid #ccc; border:none; text-align:center;" value="2024.12"> 까지의 매출액 (B): 
                            <input type="text" style="width:100px; border-bottom:1px solid #ccc; border:none; text-align:right; font-weight:bold; color:#0033ff;" value="1,500,000,000"> 원
                            <div class="caption">* (B)가 기준액 (C: 피보험자수 × 1,900만원)보다 큰 경우 적격</div>
                        </td>
                    </tr>
                </table>

                <div class="section-title">3. 채용 계획</div>
                <table>
                    <tr>
                        <th rowspan="2" width="15%">채용예정<br>인원</th>
                        <td width="25%">총 인원: <input type="text" style="width:30px; border-bottom:1px solid #000; border:none; text-align:center; color:#0033ff; font-weight:bold;" value="5"> 명</td>
                        <th width="15%">근로계약<br>형태</th>
                        <td width="45%"><input type="text" class="input-box" value="정규직" style="background:none; text-align:left;"></td>
                    </tr>
                    <tr>
                        <td>
                            수도권: <input type="text" style="width:20px; border:none; font-weight:bold; color:#0033ff;" value="5"> / 비수도권: <input type="text" style="width:20px; border:none; font-weight:bold; color:#0033ff;" value="0">
                            <br><span style="font-size:10px; color:#666;">(일반 3 / 우대 1 / 특별 1)</span>
                        </td>
                        <th>근무시간</th>
                        <td class="text-left">
                            주 <input type="text" style="width:25px; border-bottom:1px solid #000; border:none; text-align:center; font-weight:bold; color:#0033ff;" value="40"> 시간<br>
                            월급여: <input type="text" style="width:80px; border-bottom:1px solid #000; border:none; text-align:right; font-weight:bold; color:#0033ff;" value="2,500,000"> 원
                        </td>
                    </tr>
                </table>

                <div style="border: 1.2px solid #000; padding: 10px; margin-top: 5px;">
                    <div style="font-weight:bold; margin-bottom:8px; font-size:10.5px;">
                        <input type="checkbox" checked> 동 사업으로 지원받고자 하는 청년을 참여신청일 직전 3개월 이내 먼저 채용한 경우
                    </div>
                    <table style="margin-bottom:0; border:1px solid #ccc;">
                        <tr style="background:#f9f9f9; text-align:center; font-size:10px;">
                            <td width="30%">성 명</td><td width="70%">채 용 일</td>
                        </tr>
                        <tr>
                            <td><input type="text" class="input-box" value="홍길동" style="background:none;"></td>
                            <td><input type="text" class="input-box" value="2026년 01월 15일" style="background:none;"></td>
                        </tr>
                    </table>
                </div>

                <div class="section-title">4. 담당자 정보</div>
                <table>
                    <tr>
                        <th width="15%">담당부서</th><td width="35%"><input type="text" class="input-box" value="인사팀" style="text-align:left;"></td>
                        <th width="15%">담당자명</th><td width="35%"><input type="text" class="input-box" value="김뚝딱" style="text-align:left;"></td>
                    </tr>
                    <tr>
                        <th>전화번호</th><td><input type="text" class="input-box" value="02-1234-5678" style="text-align:left;"></td>
                        <th>이메일</th><td><input type="text" class="input-box" value="admin@ludi.com" style="text-align:left;"></td>
                    </tr>
                </table>

                <div style="margin-top:40px; text-align:center;">
                    <p>2026년 03월 24일</p>
                    <div style="display:flex; justify-content: flex-end; margin-top:20px; padding-right:40px; font-weight:bold;">
                        <span>신청인(대표자) : 윤재찬 (서명)</span>
                    </div>
                </div>
            </div>
        </div>
        """

        components.html(form1_html, height=1100, scrolling=True)

        if st.button("✅ 신청서 확정", type="primary", use_container_width=True):
            st.success("참여 신청서가 저장되었습니다.")

    # ------------------------------------------------------------------
    # 서식 - 지급 신청서 기업용
    # ------------------------------------------------------------------
    else:
        st.subheader("📄 지급 신청서 및 확인서")

        form7_html = f"""
            <div style="background-color: #525659; padding: 30px; display: flex; flex-direction: column; align-items: center; gap: 40px;">
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
                .pdf-page {{
                    width: 820px;
                    background-color: white;
                    padding: 50px 60px;
                    font-family: 'Malgun Gothic', 'Noto Sans KR', sans-serif;
                    color: black;
                    font-size: 11px;
                    line-height: 1.5;
                    box-shadow: 0 0 10px rgba(0,0,0,0.5);
                    position: relative;
                }}
                .main-title {{ text-align: center; font-size: 19px; font-weight: bold; margin: 15px 0; text-decoration: underline; }}
                .section-title {{ font-size: 12px; font-weight: bold; margin: 20px 0 5px 0; background: #f2f2f2; padding: 4px 10px; border-left: 4px solid #333; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 10px; border: 1.2px solid #000; table-layout: fixed; }}
                th, td {{ border: 1px solid #000; padding: 6px 4px; font-size: 10px; text-align: center; vertical-align: middle; }}
                th {{ background-color: #f8f8f8; font-weight: bold; }}
                .text-left {{ text-align: left; padding-left: 8px; }}
                .input-box {{ width: 95%; border: none; outline: none; background: #f0f7ff; font-weight: bold; color: #0033ff; font-size: 10.5px; text-align: center; }}
                .input-inline {{ border: none; border-bottom: 1px solid #000; outline: none; width: 45px; text-align: center; font-weight: bold; color: #0033ff; background: transparent; }}
                .check-container {{ display: flex; justify-content: center; gap: 15px; white-space: nowrap; }}
                .check-item {{ display: inline-flex; align-items: center; gap: 5px; cursor: pointer; }}
                input[type="checkbox"] {{ cursor: pointer; width: 14px; height: 14px; margin: 0; }}
                .sub-desc {{ font-size: 9px; color: #555; padding-left: 15px; line-height: 1.3; display: block; margin-top: 2px; text-align: left; }}
            </style>

            <div class="pdf-page">
                <div style="text-align: right; font-weight: bold;">■ [서식 7]</div>
                <table style="width: 100%; border: 1px solid #000; margin-bottom: 10px;">
                    <tr>
                        <td width="15%" style="background:#f2f2f2;">접수번호</td>
                        <td width="35%"><input type="text" class="input-box" value="○○기관 - 2026 - 0000"></td>
                        <td width="15%" style="background:#f2f2f2;">접수일자</td>
                        <td width="35%"><input type="text" class="input-box" value="2026. 03. 24."></td>
                    </tr>
                </table>

                <div class="main-title">『청년일자리도약장려금』 지급 신청서(기업용)</div>
                <p style="text-align: right; font-size: 10px;">※ [  ]에는 해당되는 곳에 √표를 합니다.</p>

                <div class="section-title">1. 사업장 기본 정보</div>
                <table>
                    <tr>
                        <th width="15%">사업장명</th><td width="35%"><input type="text" class="input-box" value="{company_name}" style="text-align:left;"></td>
                        <th width="15%">대표자명</th><td width="35%"><input type="text" class="input-box" value="{ceo_name}" style="text-align:left;"></td>
                    </tr>
                    <tr>
                        <th>사업자등록번호</th><td><input type="text" class="input-box" value="{biz_no}" style="text-align:left;"></td>
                        <th>법인등록번호</th><td><input type="text" class="input-box" value="2022-222222" style="text-align:left;"></td>
                    </tr>
                    <tr>
                        <th>고용보험 관리번호</th><td><input type="text" class="input-box" value="987-65-43210" style="text-align:left;"></td>
                        <th>소재지</th><td><input type="text" class="input-box" value="{address}" style="text-align:left;"></td>
                    </tr>
                </table>

                <div class="section-title">2. 신청 내용</div>
                <table>
                    <tr style="background:#f8f8f8;">
                        <th width="20%">성 명<br>(주민번호)</th>
                        <th width="15%">채용일*<br>(년월일)</th>
                        <th width="10%">신청<br>회차</th>
                        <th width="35%">신청기간<br>(년월일 ~ 년월일)</th>
                        <th width="20%">신청금액<br>(원)</th>
                    </tr>
                    <tr>
                        <td><input type="text" class="input-box" value="홍길동 (950101-1******)"></td>
                        <td><input type="text" class="input-box" value="2026.02.01"></td>
                        <td><input type="text" class="input-box" value="1"></td>
                        <td><input type="text" class="input-box" value="2026.02.01 ~ 2026.02.28"></td>
                        <td><input type="text" class="input-box" value="600,000"></td>
                    </tr>
                    <tr>
                        <td><input type="text" class="input-box" value="홍길동 (950101-1******)"></td>
                        <td><input type="text" class="input-box" value="2026.02.01"></td>
                        <td><input type="text" class="input-box" value="1"></td>
                        <td><input type="text" class="input-box" value="2026.02.01 ~ 2026.02.28"></td>
                        <td><input type="text" class="input-box" value="600,000"></td>
                    </tr>
                           <tr>
                        <td><input type="text" class="input-box" value="홍길동 (950101-1******)"></td>
                        <td><input type="text" class="input-box" value="2026.02.01"></td>
                        <td><input type="text" class="input-box" value="1"></td>
                        <td><input type="text" class="input-box" value="2026.02.01 ~ 2026.02.28"></td>
                        <td><input type="text" class="input-box" value="600,000"></td>
                    </tr>
                </table>

                <div class="section-title">3. 지급 계좌 및 고용조정 확인</div>
                <table>
                    <tr>
                        <th width="25%">기업명의 계좌번호</th>
                        <td colspan="3" class="text-left">
                            (<input type="text" class="input-inline" style="width:60px;" value="○○">) 은행 
                            <input type="text" class="input-inline" style="width:150px;" value="123-456-789012">
                            (예금주 : <input type="text" class="input-inline" style="width:80px;" value="주식회사 루디"> )
                        </td>
                    </tr>
                    <tr>
                        <th>고용조정<br>이직 발생여부</th>
                        <td colspan="3">
                            <div class="check-container">
                                <label class="check-item"><input type="checkbox"> 예</label>
                                <label class="check-item"><input type="checkbox" checked> 아니오</label>
                            </div>
                        </td>
                    </tr>
                </table>

                <div style="margin-top:50px; text-align:center;">
                    <p>2026년 03월 24일</p>
                    <div style="display:flex; justify-content: flex-end; margin-top:30px; padding-right:40px; font-weight:bold;">
                        <span>신청인(대표자) : {ceo_name} (서명)</span>
                    </div>
                </div>
            </div>

            <div class="pdf-page">
                <div style="text-align: right; font-weight: bold;">■ [서식 7-1]</div>
                <div class="main-title">사업주 확인서 (지원금 신청 시)</div>
                
                <div class="section-title">1. 참여 자격 제한 사유 해당 여부</div>
                <table>
                    <tr style="background:#f8f8f8;"><th width="75%">지원제외 기업이 아님을 확인 (지급 신청일 기준)</th><th width="25%">해당 여부</th></tr>
                    <tr><td>① 소비·향락업</td><td class="check-container"><label class="check-item"><input type="checkbox"> 예</label><label class="check-item"><input type="checkbox" checked> 아니오</label></td></tr>
                    <tr><td>② 국가기관, 지방자치단체, 공공기관, 학교 등</td><td class="check-container"><label class="check-item"><input type="checkbox"> 예</label><label class="check-item"><input type="checkbox" checked> 아니오</label></td></tr>
                    <tr><td>③ 임금체불 명단 공개 중인 사업주 등</td><td class="check-container"><label class="check-item"><input type="checkbox"> 예</label><label class="check-item"><input type="checkbox" checked> 아니오</label></td></tr>
                    <tr><td>④ 중대재해 발생 명단 공표 사업장</td><td class="check-container"><label class="check-item"><input type="checkbox"> 예</label><label class="check-item"><input type="checkbox" checked> 아니오</label></td></tr>
                    <tr><td>⑤ 지원금 지급제한 기간 내에 있는 사업주</td><td class="check-container"><label class="check-item"><input type="checkbox"> 예</label><label class="check-item"><input type="checkbox" checked> 아니오</label></td></tr>
                    <tr><td>⑥ 고용보험료 체납기업</td><td class="check-container"><label class="check-item"><input type="checkbox"> 예</label><label class="check-item"><input type="checkbox" checked> 아니오</label></td></tr>
                    <tr><td>⑦ 채용일 전후 고용조정 이직이 있는 사업장</td><td class="check-container"><label class="check-item"><input type="checkbox"> 예</label><label class="check-item"><input type="checkbox" checked> 아니오</label></td></tr>
                    <tr><td>⑧ 기타 지침상 지원제외 기업</td><td class="check-container"><label class="check-item"><input type="checkbox"> 예</label><label class="check-item"><input type="checkbox" checked> 아니오</label></td></tr>
                </table>

                <div class="section-title">2. 지원대상 청년 요건을 확인</div>
                <table>
                    <tr style="background:#f8f8f8;"><th width="75%">확인 항목</th><th width="25%">해당 여부</th></tr>
                    <tr><td>① 채용일 현재 청년(만 15~34세)</td><td class="check-container"><label class="check-item"><input type="checkbox" checked> 예</label><label class="check-item"><input type="checkbox"> 아니오</label></td></tr>
                    <tr><td>② 채용일 현재 취업 중이 아닌 자</td><td class="check-container"><label class="check-item"><input type="checkbox" checked> 예</label><label class="check-item"><input type="checkbox"> 아니오</label></td></tr>
                    <tr><td>③ 정규직, 고용보험, 최저임금 등 근로조건 충족</td><td class="check-container"><label class="check-item"><input type="checkbox" checked> 예</label><label class="check-item"><input type="checkbox"> 아니오</label></td></tr>
                    <tr><td>④ 대표자의 배우자 또는 직계 존비속이 아님</td><td class="check-container"><label class="check-item"><input type="checkbox" checked> 예</label><label class="check-item"><input type="checkbox"> 아니오</label></td></tr>
                    <tr><td>⑤ 대한민국 국적 보유자</td><td class="check-container"><label class="check-item"><input type="checkbox" checked> 예</label><label class="check-item"><input type="checkbox"> 아니오</label></td></tr>
                    <tr><td>⑥ 1년 이내 재고용 해당하지 않음</td><td class="check-container"><label class="check-item"><input type="checkbox" checked> 예</label><label class="check-item"><input type="checkbox"> 아니오</label></td></tr>
                    <tr><td>⑦ 타 인건비 지원금 중복 수령하지 않음</td><td class="check-container"><label class="check-item"><input type="checkbox" checked> 예</label><label class="check-item"><input type="checkbox"> 아니오</label></td></tr>
                    <tr><td>⑧ 고등학교/대학교 재학 중인 자가 아님</td><td class="check-container"><label class="check-item"><input type="checkbox" checked> 예</label><label class="check-item"><input type="checkbox"> 아니오</label></td></tr>
                </table>

                <div style="border: 1.2px solid #000; padding: 15px; margin-top: 20px; background: #fdfdfd; text-align:center;">
                    <p>부정한 방법으로 지원금 수령 시 불이익을 감수할 것을 확인합니다.</p>
                    <label class="check-item"><input type="checkbox" checked> 예</label>
                    <label class="check-item" style="margin-left:20px;"><input type="checkbox"> 아니오</label>
                </div>
                
                <div style="margin-top:40px; text-align:center;">
                    <p>2026년 03월 24일</p>
                    <div style="display:flex; justify-content: flex-end; margin-top:20px; padding-right:40px; font-weight:bold;">
                        <span>확인자(대표자) : {ceo_name} (서명)</span>
                    </div>
                </div>
            </div>
        </div>
        
        """
        

        components.html(form7_html, height=1100, scrolling=True)

        if st.button("✅ 지급 신청서 확정", type="primary", use_container_width=True):
            st.success("지급 신청서가 저장되었습니다.")

    # 하단 이동 버튼
    st.markdown("<hr class='dd-divider'>", unsafe_allow_html=True)
    if st.button("← 지원금 결과로 돌아가기"):
        st.session_state.page = "results"
        st.rerun()
