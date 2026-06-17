"""Deterministic policy source text preprocessing.

The crawled worklife.kr policy pages wrap the real policy body in large blocks
of site navigation, search/hashtag banners, breadcrumb buttons, and an address/
copyright footer. This noise dilutes the extraction model's attention and is a
common source of non-policy "evidence".

`preprocess_policy_source_text` removes that chrome and normalizes whitespace.
It MUST NOT alter policy facts: it only drops navigation/footer/button lines and
collapses whitespace. It never reorders, rewrites, merges, or invents body words,
so any evidence substring inside the body stays an exact (whitespace-normalized)
substring of the cleaned text.

The cleaned text is intended to be used for BOTH the extraction prompt and the
candidate evidence validation, so both sides reference the same canonical source.
"""

from typing import List


# Header boundary: the policy body title follows the first "신청하러 가기" button.
HEADER_BOUNDARY_ANCHOR = "신청하러 가기"

# Footer boundary: the real end-of-content marker is the agency address line
# (`30117 세종특별자치시 ...`), present in every page, followed by copyright.
# We deliberately do NOT cut at the contact line (고객상담센터), because on some
# pages the 문의/고객상담센터 block sits mid-document (before the Q&A section),
# and cutting there would drop source-backed Q&A rules.
FOOTER_ANCHORS = (
    "30117",
    "Copyright 2015",
    "All rights reserved",
    "Ministry Of Employment",
)

# Standalone chrome lines that are pure navigation / buttons / breadcrumbs.
DROP_EXACT_LINES = frozenset(
    {
        "신청하러 가기",
        "홈으로",
        "본문 바로가기",
        "주메뉴 바로가기",
        "전체메뉴",
        "통합검색",
        "검색",
        "검색어 입력",
        "문의",
        "목록",
        "이전",
        "다음",
        "예시 보기",
        "예시보기",
        "신청서 및 증빙서류",
    }
)


def preprocess_policy_source_text(raw_text: str) -> str:
    """Return the policy body with site chrome removed and whitespace normalized.

    Steps (all deterministic, content-preserving for the body):

    1. Drop the navigation header: everything up to and including the first
       ``신청하러 가기`` line. If that anchor is absent, the header is kept.
    2. Drop the footer: everything from the first footer anchor to the end.
    3. Drop standalone navigation/button/breadcrumb lines anywhere in the body.
    4. Collapse internal whitespace runs (including the HTML indentation padding)
       and drop blank lines.
    """

    lines = raw_text.splitlines()

    start = _header_start_index(lines)
    end = _footer_start_index(lines, start)
    body = lines[start:end]

    cleaned: List[str] = []
    for line in body:
        normalized = " ".join(line.split())
        if not normalized:
            continue
        if normalized in DROP_EXACT_LINES:
            continue
        cleaned.append(normalized)

    return "\n".join(cleaned)


def _header_start_index(lines: List[str]) -> int:
    for index, line in enumerate(lines):
        if HEADER_BOUNDARY_ANCHOR in line:
            return index + 1
    return 0


def _footer_start_index(lines: List[str], start: int) -> int:
    for index in range(start, len(lines)):
        if any(anchor in lines[index] for anchor in FOOTER_ANCHORS):
            return index
    return len(lines)
