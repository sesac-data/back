# import io
# from datetime import datetime
# from reportlab.pdfgen import canvas
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.ttfonts import TTFont
# from pypdf import PdfReader, PdfWriter

# # 1. 폰트 설정
# try:
#     FONT_PATH = "C:/Windows/Fonts/malgun.ttf"
#     pdfmetrics.registerFont(TTFont('Custom', FONT_PATH))
#     FONT_NAME = "Custom"
# except:
#     FONT_NAME = "Helvetica"

# # 2. [서식 1] 확장 좌표 설정
# COORD_MAP_FORM_1 = {
#     "receipt_date": (350, 630),
#     "footer_date_year":  (400, 140),
#     "footer_date_month":  (430, 140),
#     "footer_date_day":  (460, 140),
#     "footer_ceo":   (450, 125),

#     # 1. 사업장 현황
#     "biz_name":     (190, 600),
#     "biz_no":       (188, 588),
#     "biz_type":     (180, 570),
#     "corp_no":      (380, 588),
#     "ceo_name":     (390, 600),
#     "biz_manage_no": (390, 570),
#     "address_box":  (170, 553, 300, 15),

#     # 2. 기업 구분
#     "check_boxes": {
#         "priority": (127, 440),
#         "knowledge": (127, 430),
#         "culture": (220, 430),
#         "future": (127, 420),
#         "renewable": (310, 430),
#         "startup": (413, 430),
#         "local": (208, 420),
#         "crisis": (288, 420), 
#         "special": (390, 420)           
#     },

#  # 3. 채용 계획 (원하시는 형태의 개별 좌표 매핑)
#     # 형식: "데이터키": (x좌표, y좌표)
#     "hiring_coords": {
#         "count": (230, 315),     # x: 230, y: 320
#         "in": (230, 305),        # x: 230, y: 300
#         "not_in": (230, 293),    # x: 230, y: 290
#         "time": (230, 260),      # x: 230, y: 260
#         "type": (420, 300),      # x: 420, y: 300
#         "salary": (430, 260)     # x: 270, y: 430
#     },

#     # 4. 담당자 정보
#     "staff_dept":   (170, 190),
#     "staff_name":   (370, 190),
#     "staff_email_box": (370, 175, 100, 15),
#     "staff_fax":    (170, 170)
# }

# def draw_fit_text(can, text, x, y, width, max_font=10, align="center"):
#     font_size = max_font
#     text_str = str(text)
#     while font_size > 4:
#         text_width = pdfmetrics.stringWidth(text_str, FONT_NAME, font_size)
#         if text_width <= width:
#             break
#         font_size -= 0.5
    
#     can.setFont(FONT_NAME, font_size)
#     if align == "center":
#         can.drawCentredString(x + (width/2), y, text_str)
#     else:
#         can.drawString(x, y, text_str)

# def generate_form_1_full(input_pdf, output_pdf, data):
#     reader = PdfReader(input_pdf)
#     writer = PdfWriter()
#     packet = io.BytesIO()
#     can = canvas.Canvas(packet, pagesize=(595.27, 841.89))

#     today = datetime.now()
#     date_str = today.strftime("%Y. %m. %d.")

#     # --- 1. 기본 정보 & 날짜 ---
#     can.setFont(FONT_NAME, 10)
#     can.drawCentredString(*COORD_MAP_FORM_1["receipt_date"], date_str)
#     can.drawCentredString(*COORD_MAP_FORM_1["footer_date_year"], str(today.year))
#     can.drawCentredString(*COORD_MAP_FORM_1["footer_date_month"], str(today.month))
#     can.drawCentredString(*COORD_MAP_FORM_1["footer_date_day"], str(today.day))
#     can.drawCentredString(*COORD_MAP_FORM_1["footer_ceo"], str(data.get("ceo_name", "")))

#     can.setFont(FONT_NAME, 9)
#     for k in ["biz_name", "biz_no", 'biz_type', 'corp_no', "ceo_name", "biz_manage_no", "staff_dept", "staff_name", "staff_fax"]:
#         if data.get(k):
#             can.drawString(*COORD_MAP_FORM_1[k], str(data[k]))

#     # --- 2. 기업 구분 (중복 체크) ---
#     can.setFont("Helvetica", 12) 
#     selected_categories = data.get("categories", [])
#     for cat in selected_categories:
#         if cat in COORD_MAP_FORM_1["check_boxes"]:
#             can.drawString(*COORD_MAP_FORM_1["check_boxes"][cat], "v")

#     # --- 3. 채용 계획 (전달받은 개별 좌표로 하나씩 출력) ---
#     can.setFont(FONT_NAME, 9)
#     h_data = data.get("hiring_plans", {}) # 리스트가 아닌 딕셔너리로 가정
#     h_coords = COORD_MAP_FORM_1["hiring_coords"]

#     # 각 키값이 데이터에 있으면 정해진 좌표에 출력
#     for key, coord in h_coords.items():
#         if key in h_data:
#             # *coord를 사용하여 (x, y)를 풀어서 전달
#             can.drawCentredString(*coord, str(h_data[key]))

#     # --- 4. 박스 영역 ---
#     if data.get("address"):
#         x, y, w, h = COORD_MAP_FORM_1["address_box"]
#         draw_fit_text(can, data["address"], x, y, w, align="left")
#     if data.get("email"):
#         x, y, w, h = COORD_MAP_FORM_1["staff_email_box"]
#         draw_fit_text(can, data["email"], x, y, w, align="left")

#     can.save()
#     packet.seek(0)
    
#     guide_pdf = PdfReader(packet)
#     page = reader.pages[0]
#     page.merge_page(guide_pdf.pages[0])
#     writer.add_page(page)

#     for i in range(1, len(reader.pages)):
#         writer.add_page(reader.pages[i])

#     with open(output_pdf, "wb") as f:
#         writer.write(f)
#     print(f"✅ 생성 완료: {output_pdf}")

# if __name__ == "__main__":
#     complex_data = {
#         "biz_name": "주식회사 루디",
#         "biz_no": "123-45-67890",
#         "biz_type": "의류, 패션, IT, 짱짱맨",
#         "corp_no" : '20-222-2222',
#         "ceo_name": "윤재찬",
#         "biz_manage_no": "987-65-43210",
#         "address": "서울시 강남구 테헤란로 루디빌딩 7층",
#         "categories": ["priority", "knowledge", "culture", "future", "renewable", "startup", "local", "crisis", "special"], 
#         "hiring_plans": {
#             "count": "5명",
#             "in": "5명",
#             "not_in": "해당없음",
#             "time": "40시간",
#             "type": "정규직",
#             "salary": "250만원"
#         },
#         "staff_dept": "인사팀",
#         "staff_name": "홍길동",
#         "email": "hr_manager_ludi@ludi.ai",
#         "staff_fax": "02-123-4567"
#     }
    
#     generate_form_1_full("./청일도_신청서_운영기관(수정).pdf", "./final_form1_complete.pdf", complex_data)

import io
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter

# 1. 폰트 설정
try:
    FONT_PATH = "C:/Windows/Fonts/malgun.ttf"
    pdfmetrics.registerFont(TTFont('Custom', FONT_PATH))
    FONT_NAME = "Custom"
except:
    FONT_NAME = "Helvetica"

# 2. [서식 1] 확장 좌표 설정
COORD_MAP_FORM_1 = {
    "receipt_date": (350, 630),
    "footer_date_year":  (400, 140),
    "footer_date_month":  (430, 140),
    "footer_date_day":  (460, 140),
    "footer_ceo":   (450, 125),

    # 1. 사업장 현황
    "biz_name":      (190, 600),
    "biz_no":        (188, 588),
    "biz_type":      (180, 570),
    "corp_no":       (380, 588),
    "ceo_name":      (390, 600),
    "biz_manage_no": (390, 570),
    "address_box":   (170, 553, 300, 15),
    
    # --- [추가] 2. 기업 구분 섹션: 월별 피보험자 수 좌표 관련 ---
    "monthly_insurance_start_x": 150,   # 1월 위치
    "monthly_insurance_y": 480,        # 피보험자 수 행 높이
    "monthly_insurance_step_x": 28,  # 칸 사이 간격
    
    # --- [추가] 2. 기업 구분 섹션: 월별 피보험자 수 좌표 관련 ---
    "monthly_insurance_start_x": 155,   # 1월 위치
    "monthly_insurance_y": 460,        # 피보험자 수 행 높이
    "monthly_insurance_step_x": 28,  # 칸 사이 간격

    # --- [추가] 2. 기업 구분 하단 데이터 ---
    "avg_insurance_count": (400, 525), # 평균 피보험자 수 (명)
    "sales_period_from":   (240, 390), # 매출 과세 기간 (부터)
    "sales_period_to":     (320, 390), # 매출 과세 기간 (까지)
    "sales_period":        (422, 390), # 매출액
    "sales_converted":     (260, 380), # 연 매출액 환산 (C)
    'insurance_count':     (220, 370), # 기준 피보험자수
    "sales_amount":        (350, 370), # 매출액 (B)

    "check_boxes": {
        "priority": (127, 440),
        "knowledge": (127, 430),
        "culture": (220, 430),
        "future": (127, 420),
        "renewable": (310, 430),
        "startup": (413, 430),
        "local": (208, 420),
        "crisis": (288, 420), 
        "special": (390, 420)           
    },

    # 3. 채용 계획 (상단)
    "hiring_coords": {
        "count": (230, 315), 
        "in": (230, 305), 
        "not_in": (230, 293),
        "time": (230, 263), 
        "type": (420, 300), 
        "salary": (430, 260)
    },

    # --- [추가] 3-1. 채용 계획 하단 (선채용 명단) ---
    "pre_hiring_check": (465, 248),  # 선채용 해당 시 체크박스
    "pre_hiring_name":  (210, 235), # 성명
    "pre_hiring_date":  (430, 235), # 채용일

    # 4. 담당자 정보
    "staff_dept":   (170, 190),
    "staff_name":   (370, 190),
    "staff_email_box": (370, 175, 100, 15),
    "staff_fax":    (170, 170)
}

def draw_fit_text(can, text, x, y, width, max_font=10, align="center"):
    font_size = max_font
    text_str = str(text)
    while font_size > 4:
        text_width = pdfmetrics.stringWidth(text_str, FONT_NAME, font_size)
        if text_width <= width:
            break
        font_size -= 0.5
    
    can.setFont(FONT_NAME, font_size)
    if align == "center":
        can.drawCentredString(x + (width/2), y, text_str)
    else:
        can.drawString(x, y, text_str)

def generate_form_1_full(input_pdf, output_pdf, data):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(595.27, 841.89))

    today = datetime.now()
    date_str = today.strftime("%Y. %m. %d.")

    # --- 1. 기본 정보 & 날짜 ---
    can.setFont(FONT_NAME, 10)
    can.drawCentredString(*COORD_MAP_FORM_1["receipt_date"], date_str)
    can.drawCentredString(*COORD_MAP_FORM_1["footer_date_year"], str(today.year))
    can.drawCentredString(*COORD_MAP_FORM_1["footer_date_month"], str(today.month))
    can.drawCentredString(*COORD_MAP_FORM_1["footer_date_day"], str(today.day))
    can.drawCentredString(*COORD_MAP_FORM_1["footer_ceo"], str(data.get("ceo_name", "")))

    can.setFont(FONT_NAME, 9)
    for k in ["biz_name", "biz_no", 'biz_type', 'corp_no', "ceo_name", "biz_manage_no", "staff_dept", "staff_name", "staff_fax"]:
        if data.get(k):
            can.drawString(*COORD_MAP_FORM_1[k], str(data[k]))

    # --- [추가] 2. 피보험자 수 및 매출액 출력 ---
    if data.get("avg_insurance_count"):
        can.drawCentredString(*COORD_MAP_FORM_1["avg_insurance_count"], str(data["avg_insurance_count"]))
    
    for f in ["sales_period_from", "sales_period_to", "sales_period", "sales_amount", "sales_converted", "insurance_count"]:
        if data.get(f):
            can.drawCentredString(*COORD_MAP_FORM_1[f], str(data[f]))

    # --- [신규 추가] 월별 피보험자 수 출력 로직 ---
    monthly_counts = data.get("monthly_insurance_counts", [])
    start_x = COORD_MAP_FORM_1["monthly_insurance_start_x"]
    y_pos = COORD_MAP_FORM_1["monthly_insurance_y"]
    step_x = COORD_MAP_FORM_1["monthly_insurance_step_x"]
    for i, count in enumerate(monthly_counts[:12]):
        curr_x = start_x + (i * step_x)
        can.drawCentredString(curr_x, y_pos, str(count))

    # --- 2. 기업 구분 (중복 체크) ---
    can.setFont("Helvetica", 12) 
    selected_categories = data.get("categories", [])
    for cat in selected_categories:
        if cat in COORD_MAP_FORM_1["check_boxes"]:
            can.drawString(*COORD_MAP_FORM_1["check_boxes"][cat], "v")

    # --- 3. 채용 계획 ---
    can.setFont(FONT_NAME, 9)
    h_data = data.get("hiring_plans", {})
    h_coords = COORD_MAP_FORM_1["hiring_coords"]
    for key, coord in h_coords.items():
        if key in h_data:
            can.drawCentredString(*coord, str(h_data[key]))

    # --- [추가] 3-1. 하단 선채용 명단 출력 ---
    if data.get("pre_hired_info"):
        pre = data["pre_hired_info"]
        can.setFont("Helvetica", 12)
        can.drawString(*COORD_MAP_FORM_1["pre_hiring_check"], "v") # 체크박스 표시
        
        can.setFont(FONT_NAME, 9)
        can.drawCentredString(*COORD_MAP_FORM_1["pre_hiring_name"], str(pre.get("name", "")))
        can.drawCentredString(*COORD_MAP_FORM_1["pre_hiring_date"], str(pre.get("date", "")))

    # --- 4. 박스 영역 ---
    if data.get("address"):
        x, y, w, h = COORD_MAP_FORM_1["address_box"]
        draw_fit_text(can, data["address"], x, y, w, align="left")
    if data.get("email"):
        x, y, w, h = COORD_MAP_FORM_1["staff_email_box"]
        draw_fit_text(can, data["email"], x, y, w, align="left")

    can.save()
    packet.seek(0)
    
    guide_pdf = PdfReader(packet)
    page = reader.pages[0]
    page.merge_page(guide_pdf.pages[0])
    writer.add_page(page)

    for i in range(1, len(reader.pages)):
        writer.add_page(reader.pages[i])

    with open(output_pdf, "wb") as f:
        writer.write(f)
    print(f"✅ 생성 완료: {output_pdf}")

if __name__ == "__main__":
    complex_data = {
        "biz_name": "주식회사 루디",
        "biz_no": "123-45-67890",
        "biz_type": "의류, 패션, IT",
        "corp_no" : '20-222-2222',
        "ceo_name": "윤재찬",
        "biz_manage_no": "987-65-43210",
        "address": "서울시 강남구 테헤란로 루디빌딩 7층",
        "categories": ["priority", "knowledge", "culture", "future", "renewable", "startup", "local", "crisis", "special"], 
        
        # [데이터 추가] 2. 피보험자 및 매출액
        "monthly_insurance_counts": ["10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21"],
        "avg_insurance_count": "15",
        "sales_period_from": "2024.01",
        "sales_period_to": "2024.12",
        "sales_period" : "500,000,000",
        "sales_amount": "500,000,000",
        "insurance_count": '7',
        "sales_converted": "500,000,000",

        "hiring_plans": {
            "count": "5명", "in": "5명", "not_in": "해당없음",
            "time": "40", "type": "정규직", "salary": "2,500,000"
        },
        
        # [데이터 추가] 3-1. 선채용 정보
        "pre_hired_info": {
            "name": "홍길동",
            "date": "2026.02.01"
        },

        "staff_dept": "인사팀",
        "staff_name": "홍길동",
        "email": "hr_manager_ludi@ludi.ai",
        "staff_fax": "02-123-4567"
    }
    
    generate_form_1_full("./청일도_신청서_운영기관(수정).pdf", "./final_form1_complete.pdf", complex_data)