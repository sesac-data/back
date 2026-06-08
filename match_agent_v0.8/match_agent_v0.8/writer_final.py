# import io
# from datetime import datetime
# from reportlab.pdfgen import canvas
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.ttfonts import TTFont
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.platypus import Paragraph
# from pypdf import PdfReader, PdfWriter

# # 1. 폰트 설정
# try:
#     FONT_PATH = "C:/Windows/Fonts/malgun.ttf"
#     pdfmetrics.registerFont(TTFont('Custom', FONT_PATH))
#     FONT_NAME = "Custom"
# except:
#     FONT_NAME = "Helvetica"

# # 2. 좌표 설정
# COORD_MAP = {
#     "biz_name": (210, 608),
#     "biz_no":   (200, 580),
#     "ceo_name": (400, 605),
#     "phone":    (415, 545),
    
#     # [이메일 해결 포인트]
#     # x, y는 사각형의 왼쪽 하단 기준입니다.
#     "email_box": (215, 528, 105, 15), # (x, y, width, height) -> 이메일 전용 박스 영역
    
#     "table_start_y": 465,
#     "row_height": 15,
#     "col_name": 100, "col_date": 210, "col_count": 280, "col_period": 350, "col_amount": 430,
#     "footer_name": (440, 215),

#     "biz_manage_no": (380, 585),
#     "address":       (180, 563),
#     "staff_name":    (245, 545),
#     "fax":           (380, 530),

#     "total_count_pos": (260, 340), 
#     "total_amount_pos": (405, 340),
#     "turnover_yes": (347, 300), 
#     "turnover_no":  (425, 300), 

#     "bank_name": (200, 320),        
#     "account_no": (260, 317),       
#     "account_holder": (420, 315),   
#     "date_year": (390, 240),
#     "date_month": (430, 240),
#     "date_day": (460, 240)
# }

# def draw_email_in_box(can, text, box_coords):
#     """
#     지정된 사각형 박스(x, y, width, height) 안에 이메일을 강제로 가둠.
#     넘치면 자동으로 폰트 크기를 줄여서 한 줄로 표기.
#     """
#     x, y, width, height = box_coords
    
#     # 10pt부터 시작해서 안 맞으면 0.5pt씩 줄임
#     current_font_size = 10
#     while current_font_size > 4:
#         text_width = pdfmetrics.stringWidth(text, FONT_NAME, current_font_size)
#         if text_width <= width:
#             break
#         current_font_size -= 0.5
    
#     # 계산된 폰트 사이즈로 중앙 정렬 출력
#     can.setFont(FONT_NAME, current_font_size)
#     # y값은 박스 높이의 중앙에 오도록 미세 조정
#     can.drawCentredString(x + (width / 2), y + 2, text)

# def generate_pdf(input_pdf, output_pdf, biz_info, data_list, acc_info, is_turnover=False):
#     reader = PdfReader(input_pdf)
#     writer = PdfWriter()
#     packet = io.BytesIO()
#     can = canvas.Canvas(packet, pagesize=(595.27, 841.89))

#     # --- 1. 기업 정보 ---
#     can.setFont(FONT_NAME, 10)
#     can.drawString(*COORD_MAP["biz_name"], biz_info["biz_name"])
#     can.drawString(*COORD_MAP["biz_no"], biz_info["biz_no"])
#     can.drawCentredString(*COORD_MAP["ceo_name"], biz_info["ceo_name"])
#     can.drawCentredString(*COORD_MAP["phone"], biz_info["phone"])
    
#     # 추가 항목들
#     can.setFont(FONT_NAME, 9)
#     can.drawString(*COORD_MAP["biz_manage_no"], biz_info.get("biz_manage_no", ""))
#     can.drawString(*COORD_MAP["address"], biz_info.get("address", ""))
#     can.drawString(*COORD_MAP["staff_name"], biz_info.get("staff_name", ""))
#     can.drawString(*COORD_MAP["fax"], biz_info.get("fax", ""))
    
#     # [이메일] 박스 제한형 함수 호출
#     draw_email_in_box(can, biz_info["email"], COORD_MAP["email_box"])

#     # --- 2. 표 데이터 ---
#     total_amt = 0
#     for i, row in enumerate(data_list):
#         curr_y = COORD_MAP["table_start_y"] - (i * COORD_MAP["row_height"])
#         can.setFont(FONT_NAME, 9)
#         can.drawCentredString(COORD_MAP["col_name"], curr_y, row['name'])
#         can.drawCentredString(COORD_MAP["col_date"], curr_y, row['date'])
#         can.drawCentredString(COORD_MAP["col_count"], curr_y, row['count'])
#         can.drawCentredString(COORD_MAP["col_period"], curr_y, row['period'])
#         amt_str = row.get('amount', '800,000')
#         can.drawCentredString(COORD_MAP["col_amount"], curr_y, amt_str)
#         try: total_amt += int(amt_str.replace(',', ''))
#         except: pass

#     # --- 3. 합계 및 체크박스 ---
#     can.setFont(FONT_NAME, 10)
#     can.drawCentredString(*COORD_MAP["total_count_pos"], str(len(data_list)))
#     can.drawCentredString(*COORD_MAP["total_amount_pos"], format(total_amt, ','))
    
#     check_pos = COORD_MAP["turnover_yes"] if is_turnover else COORD_MAP["turnover_no"]
#     if check_pos != (0, 0):
#         can.setFont("Helvetica", 12)
#         can.drawString(*check_pos, "v")

#     # --- 4. 계좌 및 날짜 ---
#     can.setFont(FONT_NAME, 10)
#     can.drawString(*COORD_MAP["bank_name"], acc_info["bank"])
#     can.drawString(*COORD_MAP["account_no"], acc_info["no"])
#     can.drawString(*COORD_MAP["account_holder"], acc_info["holder"])

#     today = datetime.now()
#     can.setFont(FONT_NAME, 11)
#     can.drawCentredString(*COORD_MAP["date_year"], str(today.year))
#     can.drawCentredString(*COORD_MAP["date_month"], f"{today.month:02d}")
#     can.drawCentredString(*COORD_MAP["date_day"], f"{today.day:02d}")
#     can.drawCentredString(*COORD_MAP["footer_name"], biz_info["ceo_name"])

#     can.save()
#     packet.seek(0)
#     page = reader.pages[0]
#     page.merge_page(PdfReader(packet).pages[0])
#     writer.add_page(page)

#     with open(output_pdf, "wb") as f:
#         writer.write(f)
#     print(f"✅ {output_pdf} 생성 완료")

# if __name__ == "__main__":
#     biz = {
#         "biz_name": "주식회사 루디", "biz_no": "123-45-67890", "ceo_name": "윤재찬", "phone": "010-1234-5678", 
#         "email": "this_is_a_very_long_test_email_to_check_box_limit@ludi.ai", 
#         "biz_manage_no": "987-65-43210", "address": "서울시 강남구", "staff_name": "홍길동", "fax": "02-123-4567"
#     }
#     acc = {"bank": "신한은행", "no": "110-123-456789", "holder": "윤재찬"}
#     emps = [{"name": "홍길동", "date": "2025.01.02", "count": "1회차", "period": "25.01.02~25.02.01", "amount": "800,000"}]
    
#     generate_pdf("./template.pdf", "./final_fixed.pdf", biz, emps, acc, is_turnover=False)


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

# 2. 좌표 설정
COORD_MAP = {
    # [추가: 상단 접수일자 - 좌표를 직접 입력하세요]
    "receipt_date": (370, 630),    # 예: (480, 720)

    "biz_name": (210, 608),
    "biz_no":   (200, 580),
    "ceo_name": (400, 605),
    "phone":    (415, 545),
    
    # [이메일 박스 영역]
    "email_box": (215, 528, 105, 15), # (x, y, width, height)
    
    "table_start_y": 465,
    "row_height": 15,
    "col_name": 100, "col_date": 210, "col_count": 280, "col_period": 350, "col_amount": 430,
    "footer_name": (440, 215),

    "biz_manage_no": (380, 585),
    "address":       (180, 563),
    "staff_name":    (245, 545),
    "fax":           (380, 530),

    "total_count_pos": (260, 340), 
    "total_amount_pos": (405, 340),
    "turnover_yes": (347, 300), 
    "turnover_no":  (425, 300), 

    "bank_name": (200, 320),        
    "account_no": (260, 317),       
    "account_holder": (420, 315),   
    
    # 하단 날짜
    "date_year": (390, 240),
    "date_month": (430, 240),
    "date_day": (460, 240)
}

def draw_email_in_box(can, text, box_coords):
    """지정된 사각형 박스 안에 이메일을 강제로 가둠 (폰트 자동 축소)"""
    x, y, width, height = box_coords
    current_font_size = 10
    while current_font_size > 4:
        text_width = pdfmetrics.stringWidth(text, FONT_NAME, current_font_size)
        if text_width <= width:
            break
        current_font_size -= 0.5
    can.setFont(FONT_NAME, current_font_size)
    can.drawCentredString(x + (width / 2), y + 2, text)

def generate_pdf(input_pdf, output_pdf, biz_info, data_list, acc_info, is_turnover=False):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(595.27, 841.89))

    today = datetime.now()

    # --- 1. 상단 접수일자 기입 (통합 버전) ---
    can.setFont(FONT_NAME, 10)
    if COORD_MAP["receipt_date"] != (0, 0):
        # 포맷은 원하시는 대로 변경 가능합니다 (예: 2024. 05. 20. 또는 2024-05-20)
        date_str = today.strftime("%Y. %m. %d.")
        can.drawCentredString(*COORD_MAP["receipt_date"], date_str)
        
    # --- 2. 기업 정보 ---
    can.setFont(FONT_NAME, 10)
    can.drawString(*COORD_MAP["biz_name"], biz_info["biz_name"])
    can.drawString(*COORD_MAP["biz_no"], biz_info["biz_no"])
    can.drawCentredString(*COORD_MAP["ceo_name"], biz_info["ceo_name"])
    can.drawCentredString(*COORD_MAP["phone"], biz_info["phone"])
    
    # 추가 항목 (관리번호, 주소, 담당자, 팩스)
    can.setFont(FONT_NAME, 9)
    can.drawString(*COORD_MAP["biz_manage_no"], biz_info.get("biz_manage_no", ""))
    can.drawString(*COORD_MAP["address"], biz_info.get("address", ""))
    can.drawString(*COORD_MAP["staff_name"], biz_info.get("staff_name", ""))
    can.drawString(*COORD_MAP["fax"], biz_info.get("fax", ""))
    
    # 이메일 박스 제한형 출력
    draw_email_in_box(can, biz_info["email"], COORD_MAP["email_box"])

    # --- 3. 표 데이터 ---
    total_amt = 0
    for i, row in enumerate(data_list):
        curr_y = COORD_MAP["table_start_y"] - (i * COORD_MAP["row_height"])
        can.setFont(FONT_NAME, 9)
        can.drawCentredString(COORD_MAP["col_name"], curr_y, row['name'])
        can.drawCentredString(COORD_MAP["col_date"], curr_y, row['date'])
        can.drawCentredString(COORD_MAP["col_count"], curr_y, row['count'])
        can.drawCentredString(COORD_MAP["col_period"], curr_y, row['period'])
        amt_str = row.get('amount', '800,000')
        can.drawCentredString(COORD_MAP["col_amount"], curr_y, amt_str)
        try: total_amt += int(amt_str.replace(',', ''))
        except: pass

    # --- 4. 합계 및 체크박스 ---
    can.setFont(FONT_NAME, 10)
    can.drawCentredString(*COORD_MAP["total_count_pos"], str(len(data_list)))
    can.drawCentredString(*COORD_MAP["total_amount_pos"], format(total_amt, ','))
    
    check_pos = COORD_MAP["turnover_yes"] if is_turnover else COORD_MAP["turnover_no"]
    if check_pos != (0, 0):
        can.setFont("Helvetica", 12)
        can.drawString(*check_pos, "v")

    # --- 5. 계좌 및 하단 날짜 ---
    can.setFont(FONT_NAME, 10)
    can.drawString(*COORD_MAP["bank_name"], acc_info["bank"])
    can.drawString(*COORD_MAP["account_no"], acc_info["no"])
    can.drawString(*COORD_MAP["account_holder"], acc_info["holder"])

    can.setFont(FONT_NAME, 11)
    can.drawCentredString(*COORD_MAP["date_year"], str(today.year))
    can.drawCentredString(*COORD_MAP["date_month"], f"{today.month:02d}")
    can.drawCentredString(*COORD_MAP["date_day"], f"{today.day:02d}")
    can.drawCentredString(*COORD_MAP["footer_name"], biz_info["ceo_name"])

    can.save()
    packet.seek(0)
    page = reader.pages[0]
    page.merge_page(PdfReader(packet).pages[0])
    writer.add_page(page)

    with open(output_pdf, "wb") as f:
        writer.write(f)
    print(f"✅ {output_pdf} 생성 완료")

if __name__ == "__main__":
    biz = {
        "biz_name": "주식회사 루디", "biz_no": "123-45-67890", "ceo_name": "윤재찬", "phone": "010-1234-5678", 
        "email": "test_email_long_address@ludi.ai", 
        "biz_manage_no": "987-65-43210", "address": "서울시 강남구", "staff_name": "홍길동", "fax": "02-123-4567"
    }
    acc = {"bank": "신한은행", "no": "110-123-456789", "holder": "윤재찬"}
    emps = [{"name": "홍길동", "date": "2025.01.02", "count": "1회차", "period": "25.01.02~25.02.01", "amount": "800,000"}]
    
    generate_pdf("./template.pdf", "./final_fixed.pdf", biz, emps, acc, is_turnover=False)