from services.policy_source_preprocessor import preprocess_policy_source_text


def _norm(value):
    return " ".join(value.split())


SAMPLE_RAW = "\n".join(
    [
        "고용노동부 일생활균형 안내",
        "본문 바로가기",
        "전체메뉴",
        "육아휴직･육아기 근로시간 단축지원금",
        "유연근무",
        "근무는 유연하게, 내 삶은 균형있게!",
        "#육아휴직",
        "전일제 근로자의 육아 사유로 근로시간 단축을 허용한 사업주를 지원합니다.",
        "신청하러 가기",
        "육아기 10시 출근 지원",
        "지원대상",
        "우선지원대상기업 사업주",
        "지원내용",
        "월 30만원",
        "                          지급일로부터 최대 1년",
        "문의",
        "고용노동부 고객상담센터(국번없이 1350)",
        "육아기 10시 출근제 Q&A",
        "Q",
        "03. 중복 사용 가능한지?",
        "A",
        "사용기간이 중복되는 경우에는 하나의 지원금만 지원 가능합니다.",
        "30117 세종특별자치시 한누리대로 422",
        "정부세종청사 11동 고용노동부",
        "Copyright 2015. Ministry Of Employment Labor. All rights reserved.",
        "홈으로",
    ]
)


def test_header_navigation_is_dropped():
    cleaned = preprocess_policy_source_text(SAMPLE_RAW)
    assert "전체메뉴" not in cleaned
    assert "#육아휴직" not in cleaned
    assert "본문 바로가기" not in cleaned
    # The body title after the first 신청하러 가기 is kept.
    assert "육아기 10시 출근 지원" in cleaned


def test_footer_is_dropped_at_address_line():
    cleaned = preprocess_policy_source_text(SAMPLE_RAW)
    assert "30117" not in cleaned
    assert "Copyright" not in cleaned
    assert "홈으로" not in cleaned


def test_midpage_qna_is_preserved():
    cleaned = preprocess_policy_source_text(SAMPLE_RAW)
    # The contact line sits before the Q&A; cutting at the address line keeps Q&A.
    assert "사용기간이 중복되는 경우에는 하나의 지원금만 지원 가능합니다." in cleaned


def test_standalone_button_and_blank_lines_are_dropped():
    cleaned = preprocess_policy_source_text(SAMPLE_RAW)
    lines = cleaned.splitlines()
    assert "신청하러 가기" not in lines
    assert "문의" not in lines
    assert all(line.strip() for line in lines)


def test_body_amounts_and_content_survive():
    cleaned = preprocess_policy_source_text(SAMPLE_RAW)
    assert "월 30만원" in cleaned
    assert "우선지원대상기업 사업주" in cleaned
    assert "지급일로부터 최대 1년" in cleaned


def test_indentation_whitespace_is_collapsed():
    cleaned = preprocess_policy_source_text(SAMPLE_RAW)
    assert "                          지급일로부터" not in cleaned
    assert "지급일로부터 최대 1년" in cleaned


def test_body_evidence_stays_substring_after_normalization():
    cleaned = preprocess_policy_source_text(SAMPLE_RAW)
    snippet = "사용기간이 중복되는 경우에는 하나의 지원금만 지원 가능합니다."
    assert _norm(snippet) in _norm(cleaned)


def test_missing_header_anchor_keeps_text():
    raw = "지원대상\n우선지원대상기업\n월 30만원"
    cleaned = preprocess_policy_source_text(raw)
    assert "지원대상" in cleaned
    assert "월 30만원" in cleaned


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
    print("test_policy_source_preprocessor passed")
