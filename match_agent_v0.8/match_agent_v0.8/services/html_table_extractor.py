"""Structure-preserving HTML to text extraction.

The existing crawler stores `target.get_text(separator="\\n")`, which discards
the 2D structure of HTML ``<table>`` elements: a grid of (row x column) cells is
flattened into a 1D sequence of lines, so the relationship between an amount cell
and its row/column header is lost. This is the root cause of the worklife table
being mis-extracted as many undifferentiated monthly_fixed items.

`extract_structured_text` keeps non-table content as plain text (same as the
crawler) but serializes each ``<table>`` as Markdown rows, so each table row stays
a single contiguous line with its cells joined by ``|``. The row/column
relationships the extraction model needs are preserved.

This module does not call the network. The recrawl script fetches HTML and passes
it here.
"""

from typing import List, Optional

from bs4 import BeautifulSoup
from bs4.element import Tag


def extract_structured_text(
    html: str,
    css_selector: Optional[str] = None,
) -> str:
    """Return target-region text with ``<table>`` elements kept as Markdown.

    Non-table content is rendered like ``get_text(separator="\\n", strip=True)``.
    Each table becomes a block of Markdown rows placed where the table appears.
    """

    soup = BeautifulSoup(html, "html.parser")

    target = (
        soup.select_one(css_selector)
        if css_selector
        else None
    ) or soup

    for table in target.find_all("table"):
        markdown = _table_to_markdown(table)
        table.replace_with(soup.new_string("\n" + markdown + "\n"))

    text = target.get_text(separator="\n", strip=True)
    return _normalize_blank_lines(text)


def _table_to_markdown(table: Tag) -> str:
    rows: List[str] = []

    for row in table.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if not cells:
            continue
        rendered = [_cell_text(cell) for cell in cells]
        rows.append("| " + " | ".join(rendered) + " |")

    return "\n".join(rows)


def _cell_text(cell: Tag) -> str:
    return " ".join(cell.get_text(separator=" ", strip=True).split())


def _normalize_blank_lines(text: str) -> str:
    lines = [line for line in (l.rstrip() for l in text.splitlines())]
    cleaned: List[str] = []
    blank = False
    for line in lines:
        if line.strip():
            cleaned.append(line)
            blank = False
        elif not blank:
            cleaned.append("")
            blank = True
    return "\n".join(cleaned).strip()
