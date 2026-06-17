from services.html_table_extractor import extract_structured_text


HTML = """
<html><body>
<div class="cont_wrap_area">
<h2>지원내용</h2>
<p>기업규모 및 도입유형에 따라 지원합니다.</p>
<table>
  <tr><th>구분</th><th>부분도입</th><th>전면도입</th></tr>
  <tr><td>50인 이상</td><td>월 20만원</td><td>월 40만원</td></tr>
  <tr><td>20~50인</td><td>월 30만원</td><td>월 50만원</td></tr>
</table>
<p>문의: 1350</p>
</div>
<div class="footer">사이트 푸터</div>
</body></html>
"""


def test_table_rows_are_preserved_as_markdown():
    text = extract_structured_text(HTML, "div.cont_wrap_area")
    lines = text.splitlines()
    # Each table row stays a single contiguous line with cells joined by |.
    assert "| 구분 | 부분도입 | 전면도입 |" in lines
    assert "| 50인 이상 | 월 20만원 | 월 40만원 |" in lines
    assert "| 20~50인 | 월 30만원 | 월 50만원 |" in lines


def test_row_keeps_size_and_amount_on_one_line():
    text = extract_structured_text(HTML, "div.cont_wrap_area")
    # The size header and its amount cells are contiguous (the relationship the
    # flattened crawler destroyed).
    for line in text.splitlines():
        if line.startswith("| 50인 이상"):
            assert "월 20만원" in line and "월 40만원" in line
            break
    else:
        raise AssertionError("size row not found")


def test_non_table_content_is_kept():
    text = extract_structured_text(HTML, "div.cont_wrap_area")
    assert "기업규모 및 도입유형에 따라 지원합니다." in text


def test_selector_scopes_to_target_region():
    text = extract_structured_text(HTML, "div.cont_wrap_area")
    assert "사이트 푸터" not in text


def test_missing_selector_falls_back_to_whole_document():
    text = extract_structured_text(HTML, "div.does_not_exist")
    assert "| 50인 이상 | 월 20만원 | 월 40만원 |" in text


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("test_html_table_extractor passed")
